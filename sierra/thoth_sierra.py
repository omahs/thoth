from sierra import config
from sierra.analyzer import all_analyzers
from sierra.analyzer.abstract_analyzer import category_classification_text
from sierra.arguments import parse_arguments
from sierra.callgraph.callgraph import SierraCallGraph
from sierra.parser.parser import SierraParser
from sierra.decompiler.decompiler import SierraDecompiler


def main() -> None:
    args = parse_arguments()

    # Show analyzers help
    if args.analyzers_help is not None:
        if args.analyzers_help:
            for analyzer_name in args.analyzers_help:
                analyzer = [
                    analyzer for analyzer in all_analyzers if analyzer.ARGUMENT == analyzer_name
                ][0]
                analyzer._print_help()
            return 0
        else:
            for analyzer in all_analyzers:
                analyzer._print_help()
            return

    # Parse a Sierra file
    sierra_file = args.file
    if sierra_file is None:
        print("You need to specify a sierra file path using the -f flag")
        return

    try:
        parser = SierraParser(config.SIERRA_LARK_PARSER_PATH)
        parser.parse(sierra_file)
    except Exception:
        print("%s is not a valid sierra file" % sierra_file)
        return

    # Control-Flow Graph
    if args.cfg:
        parser.print_cfg(folder=args.output_cfg_folder, file_format=args.format)
        return

    # Call-Graph
    if args.call:
        callgraph = SierraCallGraph(parser)
        callgraph.generate_callgraph()

        callgraph.print_callgraph(folder=args.output_callgraph_folder, file_format=args.format)
        return

    # Decompiler
    if args.decompile:
        decompiler = SierraDecompiler(program=parser)
        decompiled_code = decompiler.decompile_code()
        print(decompiled_code)
        return

    if args.analyzers is None:
        return

    # Find selected analyzers
    analyzers_names = [analyzer.ARGUMENT for analyzer in all_analyzers]
    selected_analyzers = []

    if args.analyzers:
        selected_analyzers = []
        for analyzer_name in args.analyzers:
            # Select a single analyzer
            if analyzer_name in analyzers_names:
                selected_analyzers.append(
                    [analyzer for analyzer in all_analyzers if analyzer.ARGUMENT == analyzer_name][
                        0
                    ]
                )
            # Select a whole category
            else:
                selected_category = [
                    k
                    for k, v in category_classification_text.items()
                    if v == analyzer_name.capitalize()
                ][0]
                selected_analyzers += [
                    analyzer for analyzer in all_analyzers if analyzer.CATEGORY == selected_category
                ]
    # Select all analyzers by default
    else:
        selected_analyzers = all_analyzers

    # Run analyzers
    detected_analyzers_count = 0
    for analyzer in selected_analyzers:
        detected = False
        a = analyzer(parser)
        if a._detect():
            detected = True
            detected_analyzers_count += 1
        a.print()
        if detected:
            print()

    selected_analyzers_count = len(selected_analyzers)

    print(
        "[+] %s analyzer%s %s run (%s detected)"
        % (
            selected_analyzers_count,
            "s" if selected_analyzers_count > 1 else "",
            "were" if selected_analyzers_count > 1 else "was",
            detected_analyzers_count,
        )
    )
