---
name: comment-code
description: >-
  Add code comments/docstrings or reword existing ones to match this
  codebase's terse, human-written style. Use whenever the user asks to
  comment code, document a function, add docstrings, or clean up/trim/reword
  comments — especially LLM-generated ones that read as verbose or restate
  what the code already shows. Applies to both `#` comments and docstrings.
---

# Commenting Code

In the following comment refers to both code comments and docstrings, while
docstring only refers to user facing documentation.

Use American English spelling and grammar, not British English.

## The mental model

The comments in this codebase were written by the person who wrote the code, not
by someone documenting or narrating it afterward.  An author who wrote a piece
of code understands it completely, they don't need to justify it to themselves.
They only document what helps to understand decisions or complicated aspects for
the future reader.

Write comments the same way. Before adding one, ask: would the author have added
a comment? If a competent reader of the surrounding system would find the line
self-explanatory, the answer is no. Most lines in this codebase get no comment
at all — see [AGENTS.md](../../../AGENTS.md) "Documentation".

## Why standard LLM comments are wrong

They're written from a different place: narrating the act of producing the code,
or demonstrating understanding to whoever asked for it, rather than leaving a
note for a future reader. That produces comments that restate the next line,
justify or explain mechanics the reader can already see.

The most dangerous version of this isn't verbosity, it's invented certainty or
plausible sounding explanations with no basis in the code. A guessed "why"
stated as fact is worse than no comment. If you can't confirm the reason (from
the code, or the user), don't assert one.

Example of the difference in voice, same underlying fact:

- Narrating: "Note that we need to be careful here because AltGr sends two
  separate key events, one for each of its constituent keys, and we only
  want to react to one of them."
- Authoring: "AltGr sends RAlt+RCtrl as two events, we want RAlt, ignore
  RCtrl."

## Guidlines for writing comments and docstrings

### DO

- Comments are expensive keep them short and precise, typically one or two
  lines.
- Only comment code pieces where you can answer yes to the following question.
  Would a user benefit from the comment if they are:
  - Familiar with the codebase
  - Knowledgeable about the technology being used
  - Experienced with the coding language
- Class docstrings contain the following:
  - Short, single sentence, terse summary.
  - If needed more details about behavior or usage of the class.
  - It should contextualize the class and its members, not reproduce the content
    of method documentation.
- Method and function docstrings contain the following:
  - Short summary sentence.
  - Argument and return value documentation in Google-style `Args: ...` and
    `Returns: ...`
  - Important usage-relevant details if necessary.
  - Trivial setters/getters can be omitted, but should be consistent with
    surrounding code.
- Large logic-heavy blocks require a block-level summary explaining intent
  combined with in-line comments documenting every branch of the logic flow,
  e.g.:
  ```python
  # Code above logic-heavy block.

  # Terse overview of the logic flow.
  # Check if ... holds. <-- documenting condition 1
  if <condition 1>
    <do something>
    # When X need to Y. <-- documenting condition 2
    if <condition 2>:
        <do something>
    # Failure requires Z. <-- documenting else branch
    else:
        <do something>

  # Code below logic-heavy block.
  ```
- If you document quirks and gotchas of used libraries by linking to their
  documentation.
- A truly complicated or obscure piece of code earns a longer comment with
  references to authoritative sources, if the source is third party code.
- Implementation details, IF required, are documented in the code near the
  relevant code.

### DO NOT

- Narrate or justify the code.
- Make up explanations.
- Document things that are obvious to the reader.
- Embellish or stylize comments.
- Place implementation details or complex logic explanations in docstrings, they
  belong in the code.
