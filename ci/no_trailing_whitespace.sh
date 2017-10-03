# This script checks for trailing whitespace in all files tracked by git,
# failing if it finds any. Note that (a) it removes the whitespace as a side
# effect, and (b) it will fail unless HEAD is trailing-whitespace free, even
# if the working directory is OK.

if [ "$DB" != sqlite ] ; then
	# Only run in the SQLite pass.
	exit 0
fi

cd "$(git rev-parse --show-toplevel)" # Enter the source tree root

# Remove all trailing whitespace in tracked files:
sed --in-place -e 's/ *$//' $(git ls-files)

diff="$(git diff)"

if [ -n "$diff" ] ; then
	printf 'Error: trailing whitespace found. Diff:\n\n'
	printf '%s\n' "$diff"
	exit 1
fi
