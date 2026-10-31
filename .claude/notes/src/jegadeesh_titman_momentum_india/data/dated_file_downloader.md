# dated_file_downloader.py

- A 404 or tiny response goes into not_available.txt so reruns skip holidays; any other failure is left to be retried. Several jobs on different year ranges can run at once because each skips files already on disk.
- NSE printed some old dates with two-digit years (13-Jul-20) and some index files with slashes; the parsers handle both.
