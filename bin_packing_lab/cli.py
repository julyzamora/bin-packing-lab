"""Convenience commands for the bin-packing research workflow."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request

REPO = 'julyzamora/bin-packing-lab'
URL = 'https://github.com/' + REPO


def call(args, cwd=None, capture=False, env=None):
    result = subprocess.run(args, cwd=cwd, env=env, check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else None


def checkout():
    root = Path(call(['git', 'rev-parse', '--show-toplevel'], capture=True))
    if not (root/'evaluation/Dockerfile').is_file() or not (root/'bin_packing_lab/research.py').is_file():
        raise ValueError('Run this command inside a bin-packing-lab checkout (binpack clone).')
    return root


def candidate_name(value):
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', value):
        raise argparse.ArgumentTypeError('Use a lowercase name containing letters, digits, _ or -.')
    return value


def run(args):
    root = checkout()
    queue = root/'research/queue.json'
    if args.candidate:
        source = root/'candidates'/args.candidate/'solver.py'
        if not source.is_file():
            raise ValueError(f'Missing {source.relative_to(root)}')
    if not args.no_build:
        call(['docker', 'build', '-t', 'bin-packing-evaluator:1', 'evaluation'], cwd=root)
    image = call(['docker', 'image', 'inspect', 'bin-packing-evaluator:1',
                  '--format', '{{.Id}}'], capture=True, cwd=root)
    env = dict(os.environ, EVALUATOR_IMAGE_ID=image)
    with tempfile.TemporaryDirectory() as tmp:
        if args.candidate:
            queue = Path(tmp)/'queue.json'
            queue.write_text(json.dumps({'schema': 1, 'experiments': [
                {'id': args.candidate, 'candidate': args.candidate,
                 'hypothesis': args.hypothesis or 'Local candidate evaluation'}]}))
        command = [sys.executable, '-m', 'bin_packing_lab.research', '--queue', str(queue),
                   '--max-experiments', str(args.max_experiments)]
        command += ['--require-improvement'] if args.require_improvement else ['--report-only']
        call(command, cwd=root, env=env)
    print('Evidence: runs/candidates/ (local evidence; submission CI evaluates independently).')


def submission_paths(paths):
    candidates = [p for p in paths if re.fullmatch(r'candidates/[a-z][a-z0-9_-]{0,63}/solver\.py', p)]
    if not 1 <= len(candidates) <= 3:
        raise ValueError('Submit one to three candidate solver files.')
    if any(p not in candidates and not re.fullmatch(r'research/experiments/[^/]+\.md', p) for p in paths):
        raise ValueError('Submission may change only candidate solver files and experiment Markdown notes.')
    return candidates


def submit(args):
    root = checkout()
    git = lambda *a: call(['git', *a], cwd=root, capture=True)
    if git('status', '--porcelain'):
        raise ValueError('Commit your changes first; submit requires a clean working tree.')
    branch = git('branch', '--show-current')
    if not branch or branch in ('main', 'master'):
        raise ValueError('Create and commit a candidate branch before submitting.')
    call(['gh', 'auth', 'status'], cwd=root)
    git('fetch', URL + '.git', 'main')
    base = git('rev-parse', 'FETCH_HEAD')
    paths = git('diff', '--name-only', base + '...HEAD').splitlines()
    submission_paths(paths)
    remote = git('remote', 'get-url', '--push', args.remote)
    match = re.fullmatch(r'(?:https://github\.com/|git@github\.com:)([^/]+)/([^/]+?)(?:\.git)?', remote)
    if not match:
        raise ValueError('Submission remote must be a GitHub HTTPS or SSH repository.')
    owner = match[1]
    head = owner + ':' + branch
    body = Path(args.body_file).resolve() if args.body_file else None
    if body and not body.is_file():
        raise ValueError('PR body file does not exist.')
    title = args.title or f'Candidate: {branch}'
    if args.dry_run:
        print(f'Would push {branch} to {args.remote} and open a PR against {REPO}:main.')
        print('Changed files:\n' + '\n'.join(paths))
        return
    # Existing PRs are updated by the push rather than duplicated.
    existing = json.loads(call(['gh', 'pr', 'list', '--repo', REPO, '--head', head,
                                '--state', 'open', '--json', 'url'], cwd=root, capture=True))
    call(['git', 'push', '--set-upstream', args.remote, branch], cwd=root)
    if existing:
        print(existing[0]['url']); return
    with tempfile.TemporaryDirectory() as tmp:
        if body is None:
            body = Path(tmp)/'body.md'
            body.write_text('Candidate submission through `binpack submit`.\n\n'
                            'CI will independently evaluate the exact submitted commit.\n\n'
                            'Changed files:\n' + ''.join(f'- `{p}`\n' for p in paths))
        command = ['gh', 'pr', 'create', '--repo', REPO, '--base', 'main', '--head', head,
                   '--title', title, '--body-file', str(body)]
        if args.draft:
            command.append('--draft')
        call(command, cwd=root)


def leaderboard(args):
    if args.local:
        data = json.loads((checkout()/'website/data.json').read_text())
    else:
        url = f'https://raw.githubusercontent.com/{REPO}/main/website/data.json'
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.load(response)
    if args.json:
        print(json.dumps(data, indent=2)); return
    runs = data.get('runs', [])
    if runs:
        from .leaderboard import entries
        latest = max(runs, key=lambda r: r['created_at'])
        print(f"Latest baseline run: {latest['run_id']} ({latest['created_at']})")
        print('ALGORITHM                       BINS       STATUS')
        for entry in entries([latest]):
            print(f"{entry['solver']:<32}{str(entry['bins']):<11}{entry['status']}")
    print('\nRecent candidate evaluations (separate protocol):')
    for record in sorted(data.get('candidate_runs', []), key=lambda r: r['created_at'], reverse=True)[:10]:
        print(f"{record['candidate']:<24}{record['status']:<24}{record['candidate_sha256'][:12]}")
    print('\nSynthetic benchmark evidence; not proof of optimality.')


def main(argv=None):
    parser = argparse.ArgumentParser(prog='binpack', description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    clone = sub.add_parser('clone', help='Clone the challenge repository')
    clone.add_argument('directory', nargs='?', default='bin-packing-lab')
    sub.add_parser('login', help='Authenticate using GitHub CLI')
    execute = sub.add_parser('run', help='Build the runtime and evaluate a candidate or queue')
    execute.add_argument('candidate', nargs='?', type=candidate_name)
    execute.add_argument('--hypothesis')
    execute.add_argument('--max-experiments', type=int, choices=range(1, 11), default=1)
    execute.add_argument('--no-build', action='store_true', help='Reuse the existing Docker image')
    execute.add_argument('--require-improvement', action='store_true', help='Exit nonzero for ties or rejections')
    board = sub.add_parser('leaderboard', help='Show published results')
    board.add_argument('--local', action='store_true', help='Read the checkout snapshot without network access')
    board.add_argument('--json', action='store_true')
    submit_parser = sub.add_parser('submit', help='Push the committed candidate branch and open/update its PR')
    submit_parser.add_argument('--remote', default='origin', help='Your writable GitHub remote, usually a fork')
    submit_parser.add_argument('--title')
    submit_parser.add_argument('--body-file')
    submit_parser.add_argument('--draft', action='store_true')
    submit_parser.add_argument('--dry-run', action='store_true', help='Validate and preview without pushing or opening a PR')
    args = parser.parse_args(argv)
    try:
        if args.command == 'clone':
            call(['git', 'clone', '--', URL + '.git', args.directory])
            print(f'Next: cd {args.directory} && binpack run')
        elif args.command == 'login':
            call(['gh', 'auth', 'login', '--hostname', 'github.com'])
        elif args.command == 'run':
            run(args)
        elif args.command == 'submit':
            submit(args)
        else:
            leaderboard(args)
    except FileNotFoundError as error:
        parser.exit(1, f'Missing executable or file: {error.filename}. Install Git, Docker, or GitHub CLI as needed.\n')
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'binpack: {error}\n')


if __name__ == '__main__':
    main()
