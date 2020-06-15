## Pipe Processing Language

A PPL query is a read-only requets to process semi-structured data and return results. A PPL query consists of a series of commands that are delimited by pipe ( | ) characters. The first whitespace-delimited string after each pipe character controls the command used. The remainder of the text for each command is handled in a manner specific to the given command.
PPL uses a doc flow model for the search statement. The typical structure of a statement is a composition of commands. The composition is represented by the pipe character ( ), giving the statement a very regular form that visually represents the flow of doc from left to right. Each operator accepts a doc set "from the pipe", and additional inputs from the body of the operator, then emits a doc set to the next operator that follows:
```
source=accounts
| where age > 18
| fields firstname, lastname
```

## Request for Comments (RFC)
Please add your feature requests here (New Requests)[https://github.com/penghuo/piped-processing-language/issues] and view project progress here RFCs.

## License

This project is licensed under the Apache-2.0 License.

