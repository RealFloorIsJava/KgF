"""
Part of KgF.

Author: LordKorea
"""

from html import escape


class Parser:
    """
    Used to parse templates to HTML output
    """

    # List of opening command tags
    _opening = [
        "iterate",
        "isset",
        "isnot"
    ]

    # List of closing command tags
    _closing = [
        "/iterate",
        "/isset",
        "/isnot"
    ]

    @staticmethod
    def get_template(path, symtab):
        """
        Parses the given template input to HTML.
        The given symbol table is used to resolve variables and datasets
        """
        # Get the template data
        data = ""
        with open(path) as f:
            for line in f:
                data += line

        # Parse the data
        return Parser.parse_template(data, symtab)

    @staticmethod
    def parse_template(raw, symtab):
        """ Parses template data to HTML.
        The following command tags exist:
        {OBR}           -> {
        {CBR}           -> }
        {echo xyz}      -> Print $xyz (No escaping)
        {html xyz}      -> Print $xyz (HTML escaped, for use in tags)
        {iterate xyz}   -> begin iteration through dataset xyz
                           imports entries as xyz.key
        {/iterate}      -> marks end of iteration
        {isset xyz}     -> contents are only evaluated if xyz is set
        {/isset}        -> ends isset
        {isnot xyz}     -> contents are only evaluated if xyz is not set
        {/isnot}        -> ends isnot
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
    def _modify_dataset(dataset):
        """ Removes empty sub-datasets at any depth recursively """
        for i in range(len(dataset)):
            entry = dataset[i]
            # Iterate over copy because keys are being removed inside
            for key in entry.copy():
                val = entry[key]
                if isinstance(val, list):
                    if len(val) < 1:
                        del entry[key]
                    else:
                        Parser._modify_dataset(val)

    @staticmethod
    def _fetch_tokens(raw):
        """
        Fetches the tokens in a raw sample.
        Returns a list of tokens.
        Token format:
          Text tokens: ('txt', value)
          Command tokens: ('cmd', value)

        Command tokens are added without enclosing braces
        """

        # Command mode: If true, current lexical token is a command ({...})
        command_mode = False

        # The current part of the lexical token at the cursor
        tmp = ""

        # The tokens that have been read already
        tokens = []

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
    def _create_tree(toks):
        """
        Create the AST which is used to determine the program flow.
        This is done by creating an in-memory tree and
        adding tokens to it.
        Scope tokens (Parser._opening) create new child trees.
        The parser keeps track of the current position by using a
        linked pointer tuple:
          (node, parent_pointer)
        with the parent_pointer being None for the top level node.
        The tree itself is a list with nested lists inside.

        Command tags which have their own scope are placed at the beginning of
        their scope.
        """

        # Create tree and node pointer
        syntree = []
        synptr = (syntree, None)

        # Add all tokens to the tree
        for token in toks:
            # If the pointer points outside the tree, the code is unbalanced
            if synptr is None:
                return [('txt', "Already left tree!")]

            # Get token type and value
            token_type = token[0]
            val = token[1]

            # Text tokens are simply appended to the current node
            if token_type == "txt":
                synptr[0].append(token)
            else:
                # Get command and arguments
                q = val.split(" ", 1)
                cmd = q[0]

                if cmd in Parser._closing:
                    # Step back to the parent node
                    synptr = synptr[1]
                elif cmd in Parser._opening:
                    # Create a new child tree
                    child = [token]
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
    def _parse_command(tree, symtab):
        """
        Recursively parse the given AST to generate
        the result using the given symbol table
        """
        val = ""

        if isinstance(tree, list):
            # This child is a subtree
            init = tree[0][1]  # Sub-Tree initializers are always commands

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
                for elem in tree[1:]:
                    val += Parser._parse_command(elem, symtab)

            # Iteration
            elif cmd == "iterate":
                dataset_name = args
                dataset = symtab.get(dataset_name, [])

                # Execute this nodes contents for every entry in the dataset
                for entry in dataset:
                    # Import entries
                    for key in entry:
                        symtab[dataset_name + "." + key] = entry[key]

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
                    val += var_value

                # Encoded print
                elif cmd == "html":
                    var_name = args
                    var_value = symtab.get(var_name, "%s not found" % var_name)
                    var_value = escape(var_value)
                    val += var_value
        return val