'use client';

import { Fragment } from 'react';
import { InlineMath } from 'react-katex';
import 'katex/dist/katex.min.css';

interface MathTextProps {
  text: string;
}

/**
 * Prose with LaTeX embedded in it, for Deconstruction question and answer text.
 *
 * Working lines are whole expressions handed straight to KaTeX; a question is
 * Polish sentences with fractions inside them, so the maths is marked off with
 * `$...$` (see `deconstruction._math`). A string carrying LaTeX but no `$` —
 * a revealed answer, which is a graded string and so cannot carry delimiters —
 * is rendered whole as maths. Everything else is plain text.
 */
export default function MathText({ text }: MathTextProps) {
  const segments = text.split('$');

  if (segments.length === 1) {
    return text.includes('\\') ? <InlineMath math={text} /> : <>{text}</>;
  }

  return (
    <>
      {segments.map((segment, index) =>
        index % 2 === 1 ? (
          <InlineMath key={index} math={segment} />
        ) : (
          <Fragment key={index}>{segment}</Fragment>
        ),
      )}
    </>
  );
}
