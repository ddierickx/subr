#!/usr/bin/env python

"""
    cli entry point
"""
if __name__ == "__main__":
    from tasks import SubrTask, DrySubrTask
    import argparse
    parser = argparse.ArgumentParser(description="finds subtitles for video files")
    parser.add_argument('-i', '--input', help="input video file or folder containg video files", action="append", required=True)
    parser.add_argument('-a', '--interactive', help="when the show name cannot be resolved, allow human intervention", action="store_true", required=False, default=False)
    parser.add_argument('-n', '--dryrun', help="perform a dry run, do not download subtitles but only list matches", action="store_true", required=False)
    args = parser.parse_args()

    for input in args.input:
        subrTask = DrySubrTask(input, args.interactive) if args.dryrun else SubrTask(input, args.interactive)
        subrTask.run()
