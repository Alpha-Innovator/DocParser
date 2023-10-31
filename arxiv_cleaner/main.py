from arxiv_cleaner.arguments import parse_args
from arxiv_cleaner.cleaner import Cleaner


def main():
    # Parse the arguments
    args = parse_args()

    # Create the command options
    command_options = {
        'latex': {
            'compiler': args.latex_compiler,
            'extra_args': args.latex_extra_args,
        },
        'bib': {
            'compiler': args.bib_compiler,
            'extra_args': args.bib_extra_args,
        },
        'latexpand': {
            'extra_args': args.latexpand_extra_args,
        },
    }

    # Create the cleaner
    cleaner = Cleaner(input_dir=args.input, output_dir=args.output,
                      tex=args.tex, command_options=command_options,
                      verbose=args.verbose)

    # Run the cleaner
    cleaner.clean()

    # Print the finish message
    print('Done')


if __name__ == '__main__':
    main()
