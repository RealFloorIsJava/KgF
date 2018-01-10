"""Part of Nussschale.

MIT License
Copyright (c) 2017-2018 LordKorea

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from html import escape
from typing import Any, Dict, List, Optional, Tuple, Union, cast


# A symbol table / data set.
# Note: Due to the recursive nature, it is impossible to create an exact type
# for datasets. Instead use the cast function provided below to retrieve nested
# datasets.
_DataSetCompatible = List[Dict[str, Union[str, None, Any]]]
_DataSet = List[Dict[str, Union[str, None, _DataSetCompatible]]]
_SymbolTable = Dict[str, Union[str, None, _DataSet]]


def _cast_dataset(x: Union[_DataSet, _DataSetCompatible]) -> _DataSet:
    """Provides a semi-typesafe cast for data sets.

    As the check for validity is not perfect, users should take care to not
    cast anything other than actual datasets.

    Args:
        x: The data set or data set compatible structure. Note: The name
            'data set compatible structure' is misleading, as it should be an
            actual data set even if the type says otherwise.

    Returns:
        The argument cast to a data set.
    """
    return cast(_DataSet, x)


# An abstract syntax tree.
# Note: Due to the recursive nature, it is impossible to create an exact type
# for AST nodes. Instead use the cast function provided below to retrieve
# nested AST nodes.
_Token = Tuple[str, str]
_ASTNodeCompatible = Union[_Token, List[Any]]
_ASTNode = Union[_Token, List[_ASTNodeCompatible]]
_AST = List[_ASTNode]
# Same as for AST nodes goes for _ASTPointer
_ASTPointerCompatible = Optional[Tuple[_AST, Any]]
_ASTPointer = Optional[Tuple[_AST, _ASTPointerCompatible]]


def _cast_ast_node(x: Union[_ASTNode, _ASTNodeCompatible]) -> _ASTNode:
    """Provides a semi-typesafe cast for AST nodes.

    As the check for validity is not perfect, users should take care to not
    cast anything other than actual AST nodes.

    Args:
        x: The AST node or AST node compatible structure. Note: The name 'AST
            node compatible structure' is misleading, as it should be an actual
            AST node even if the type says otherwise.

    Returns:
        The argument cast to an AST node.
    """
    return cast(_ASTNode, x)


def _cast_ast_pointer(x: Union[_ASTPointer, _ASTPointerCompatible]
                      ) -> _ASTPointer:
    """Provides a semi-typesafe cast for AST pointers.

    As the check for validity is not perfect, users should take care to not
    cast anything other than actual AST pointers.

    Args:
        x: The AST pointer or AST pointer compatible structure. Note: The name
            'AST pointer compatible structure' is misleading, as it should be
            an actual AST pointer even if the type says otherwise.

    Returns:
        The argument cast to an AST pointer.
    """
    return cast(_ASTPointer, x)


class Parser:
    """Parses templates and interprets the template language.

    The template language uses tags in curly braces to interact with the symbol
    table. The following tags exist:
    {OBR}
        Produces an opening curly brace ({)
    {CBR}
        Produces a closing curly brace (})
    {echo xyz}
        Prints the value with name 'xyz' from the symbol table. HTML tags that
        may be present in the value are not escaped.
    {html xyz}
        Prints the value with name 'xyz' from the symbol table. HTML tags and
        entities in the value are escaped.
    {iterate xyz}
        The dataset with name 'xyz' (a list of similar dicts) will be iterated.
        The template code between the opening {iterate} tag and the closing
        {/iterate} tag will be run for every dictionary in the dataset. Inside
        the tags the elements of the dataset will be imported into the symbol
        table as 'xyz.key'.
    {/iterate}
        Closes an {iterate} tag.
    {isset xyz}
        The template code between {isset} and {/isset} will be only run if
        the key 'xyz' is present in the symbol table and the associated value
        is not None.
    {/isset}
        Closes an {isset} tag.
    {isnot xyz}
        Like {isset}, but the template code is only evaluated if the key 'xyz'
        is not set or set to None.
    {/isnot}
        Closes an {isnot} tag.
    """

    # List of opening tags
    _opening = ["iterate",
                "isset",
                "isnot"]

    # List of closing tags
    _closing = ["/iterate",
                "/isset",
                "/isnot"]

    @staticmethod
    def get_template(path: str, symtab: _SymbolTable) -> str:
        """Fetches and parses the template using the given symbol table.

        Args:
            path: The path to the template file.
            symtab: The symbol table, mapping names to values.

        Returns:
            The resulting output of the template.
        """
        # Get the template data
        data = ""
        with open(path) as f:
            for line in f:
                data += line

        # Parse the data
        return Parser.parse_template(data, symtab)

    @staticmethod
    def parse_template(raw: str, symtab: _SymbolTable) -> str:
        """Parses the given template source using the given symbol table.

        Args:
            raw: The template source that should be parsed.
            symtab: The symbol table, mapping names to values.

        Returns:
            The resulting output of the template.
        """

        # Add the beginning marker to the data
        raw = "{__BEGIN}" + raw

        # Prepare symbol table (remove empty datasets)
        Parser._modify_dataset([symtab])

        # Get the tokens from the data
        tokens = Parser._fetch_tokens(raw)

        # Generate the AST
        syntree = Parser._create_tree(tokens)

        # Execute the program tree and yield results
        return Parser._parse_command(syntree, symtab)

    @staticmethod
    def _modify_dataset(dataset: _DataSet) -> None:
        """Removes empty sub-datasets at any depth recursively.

        Args:
            dataset: The dataset to modify.
        """
        for i in range(len(dataset)):
            entry = dataset[i]
            # Iterate over copy because keys are being removed inside
            for key in entry.copy():
                val = entry[key]
                if isinstance(val, list):
                    val = _cast_dataset(cast(_DataSetCompatible, val))
                    if len(val) < 1:
                        del entry[key]
                    else:
                        Parser._modify_dataset(val)

    @staticmethod
    def _fetch_tokens(raw: str) -> List[_Token]:
        """Fetches the tokens from the given source.

        There are two types of tokens, text tokens (tuples with first element
        'txt' and the second element containing the token) and command tokens
        (tuples with first element 'cmd' and the second element containing
        the token). Command tokens are used for tags. Everything that is not a
        tag will be translated to a text token.

        Args:
            raw: The template source.

        Returns:
            The flat list of tokens.
        """

        # Command mode: If true, current lexical token is a command ({...})
        command_mode = False

        # The current part of the lexical token at the cursor
        tmp = ""

        # The tokens that have been read already
        tokens = []  # type: List[_Token]

        # The cursor into the raw data
        ptr = 0

        while ptr < len(raw):
            char = raw[ptr]
            # Check if command is ending
            if command_mode and char == "}":
                command_mode = False
                # Command ended. Finish token, start next one
                if tmp != "":
                    tokens.append(('cmd', tmp))
                    tmp = ""

            # Check if command is starting
            elif not command_mode and char == "{":
                command_mode = True
                # Command started. Finish token, start next one
                if tmp != "":
                    tokens.append(('txt', tmp))
                    tmp = ""

            # Current token is expanded
            else:
                tmp += char

            # Advance cursor
            ptr += 1

        # If the last token is not empty, append it to the output
        if tmp != "":
            tokens.append(('txt', tmp))
        return tokens

    @staticmethod
    def _create_tree(toks: List[_Token]) -> _AST:
        """Creates the token AST which is used to interpret the template.

        Scope tokens (Parser._opening) create new child trees.

        Args:
            toks: The flat list of tokens.

        Returns:
            A list with nested lists representing the AST. Command tags
            that open a scope are inserted into the list used for
            representing the scope at the beginning.
        """

        # Create tree and node pointer
        syntree = []  # type: _AST
        synptr = (syntree, None)  # type: _ASTPointer

        # Add all tokens to the tree
        for token in toks:
            # If the pointer points outside the tree, the code is unbalanced
            if synptr is None:
                return [('txt', "Already left tree!")]

            # Get token type and value
            token_type = token[0]
            val = token[1]

            if token_type == "txt":
                # Text token: Append to current tree
                synptr[0].append(token)
            else:
                # Get command and arguments
                q = val.split(" ", 1)
                cmd = q[0]

                if cmd in Parser._closing:
                    # Step back to the parent node
                    synptr = _cast_ast_pointer(synptr[1])
                elif cmd in Parser._opening:
                    # Create a new child tree
                    child = [token]  # type: _AST
                    # Add the child tree and enter it
                    synptr[0].append(child)
                    synptr = (child, synptr)

                # Flat (non-scope-holding) command. Add to the current
                # tree node.
                else:
                    synptr[0].append(token)

        # 'syntree' already points to the root
        return syntree

    @staticmethod
    def _parse_command(tree: _ASTNode, symtab: _SymbolTable) -> str:
        """Parses the given AST to generate the template output.

        Args:
            tree: The AST node.
            symtab: The symbol table.

        Returns:
            The template output.
        """
        val = ""

        if isinstance(tree, list):
            # This child is a subtree
            tree = cast(_AST, tree)

            # Sub-Tree initializers are always commands
            assert isinstance(tree[0], tuple)
            init_node = tree[0]  # type: Tuple[str, str]
            init = init_node[1]

            # Get command and arguments
            q = init.split(" ", 1)
            if len(q) == 2:
                cmd, args = q
            else:
                cmd = q[0]
                args = ""

            # Handle beginning token
            if cmd == "__BEGIN":
                pass  # Template begin
                for elem in tree[1:]:  # type: _ASTNode
                    val += Parser._parse_command(elem, symtab)

            # Iteration
            elif cmd == "iterate":
                dataset_name = args
                dataset_raw = symtab.get(dataset_name, [])
                if not isinstance(dataset_raw, list):
                    raise TypeError("can't iterate over non-dataset")
                dataset = dataset_raw  # type: _DataSet

                # Execute this nodes contents for every entry in the dataset
                for entry in dataset:
                    # Import entries
                    for key in entry:
                        absolute_key = "%s.%s" % (dataset_name, key)
                        symtab[absolute_key] = entry[key]

                    # Execute contents
                    for elem in tree[1:]:
                        val += Parser._parse_command(elem, symtab)

                    # Remove entries once again
                    for key in entry:
                        del symtab[dataset_name + "." + key]

            # Is not set
            elif cmd == "isnot":
                # Note that 'not existing' also includes being set to None
                var_name = args
                var = symtab.get(var_name, None)
                if var is None:
                    for elem in tree[1:]:
                        val += Parser._parse_command(elem, symtab)

            # Is set
            elif cmd == "isset":
                # Note that 'existing' does not include being set to None
                var_name = args
                var = symtab.get(var_name, None)
                if var is not None:
                    for elem in tree[1:]:
                        val += Parser._parse_command(elem, symtab)
        else:
            # This child is a leaf of the tree
            tree = cast(_Token, tree)

            # Text node: Just add contents to result
            if tree[0] == "txt":
                val += tree[1]
            else:
                # Seperate command/arguments
                q = tree[1].split(" ", 1)
                if len(q) == 2:
                    cmd, args = q
                else:
                    cmd = q[0]
                    args = ""

                # Opening brace
                if cmd == "OBR":
                    val += "{"

                # Closing brace
                elif cmd == "CBR":
                    val += "}"

                # Print
                elif cmd == "echo":
                    var_name = args
                    var_value = symtab.get(var_name, "%s not found" % var_name)
                    if not isinstance(var_value, str):
                        raise TypeError("can't echo non-str")
                    val += var_value

                # Encoded print
                elif cmd == "html":
                    var_name = args
                    var_value = symtab.get(var_name, "%s not found" % var_name)
                    if not isinstance(var_value, str):
                        raise TypeError("can't echo (encode) non-str")
                    var_value = escape(var_value)
                    val += var_value
        return val
