# Notes

One Markdown note per source file, mirroring the source tree, holding the reasoning behind it.

- `.gitignore`: the paper's PDF is a JSTOR copy whose terms forbid redistribution, so `/paper/*.pdf` is ignored. `/data/*` is ignored except its README; rules are anchored so `src/.../site/data/` is not hidden.
- `pyproject.toml`: the `database` extra holds the TimescaleDB, MongoDB and ChromaDB drivers, kept optional so strangers can rerun the research from files alone; `tradingmachine` is the optional `live` extra.
