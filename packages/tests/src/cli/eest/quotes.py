"""List of quotes related to system design."""

import random
import textwrap

make_something_great = [
    "🎨 Simplicity is the ultimate sophistication. - Leonardo D.",
    "🖌️ Simplicity is an acquired taste. - Katharine G.",
    "💡 To create a memorable design you need to start with a thought that’s worth remembering."
    " - Thomas M.",
    "🚀 Well begun is half done. - Aristotle",
    "🖌️ Designers are crazy and yet sane enough to know where to draw the line. - Benjamin W.",
    "🌟 Creativity is piercing the mundane to find the marvelous. - Bill M.",
    "🔍 Mistakes are the portals of discovery. - James J.",
    "🧠 It’s extremely difficult to be simultaneously concerned with the end-user experience of"
    " whatever it is that you’re building and the architecture of the program that delivers that"
    "experience. - James H.",
    "🧠 Good design is a lot like clear thinking made visual. - Edward T.",
    "🚀 Innovation leads one to see the new in the old and distinguishes the ingenious from the"
    " ingenuous. - Paul R.",
    "🔮 The best way to predict the future is to invent it. - Alan K.",
    "🌟 Perfection is achieved, not when there is nothing more to add, but when there is nothing"
    " left to take away. - Antoine d.",
    "📏 You can’t improve what you don’t measure. - Tom D.",
]


def wrap_quote(quote: str, width: int = 80) -> str:
    """Wrap quote text to the given width."""
    return textwrap.fill(quote, width=width)


def box_quote(quote: str) -> str:
    """Return quote wrapped in a box with borders."""
    # Wrap the quote first
    wrapped_quote = wrap_quote(quote)

    # Calculate the width of the box
    box_width = (
        max(len(line) for line in wrapped_quote.split("\n")) + 2
    )  # +2 for side borders

    # Create top and bottom border
    top_bottom_border = "+" + "-" * (box_width) + "+"

    # Create the sides of the box
    lines = wrapped_quote.split("\n")
    boxed_lines = [f"{line.ljust(box_width - 2)}" for line in lines]

    # Return the full boxed quote
    quote = "\n".join([top_bottom_border] + boxed_lines + [top_bottom_border])
    return f"\n {quote} \n"


def get_quote() -> str:
    """
    Return random inspirational quote formatted in a box.
    """
    return box_quote(random.choice(make_something_great))
