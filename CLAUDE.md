use uv for package management and running code.
```
uv add <package>
uv run <script>
```
Use context7 MCP server to get the latest documentation of any library, this is a mandatory step before writing any code.
Dont run anything with sleep or timeout. If anything is running for a long time, move it to a background process and go and continuously monitor that task, till it is completed with some break in between in checking. Meanwhile, you can work on any other tasks. If there are none, then just keep waiting and rechecking for its completion.
