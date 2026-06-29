import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Frontmatter {
  title?: string;
  description?: string;
  date?: string;
}

const parseFrontmatter = (content: string): { frontmatter: Frontmatter; body: string } => {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) {
    return { frontmatter: {}, body: content };
  }

  const frontmatterText = match[1];
  const body = match[2].trim();
  const frontmatter: Frontmatter = {};

  for (const line of frontmatterText.split("\n")) {
    const colonIndex = line.indexOf(":");
    if (colonIndex === -1) continue;
    const key = line.slice(0, colonIndex).trim();
    let value = line.slice(colonIndex + 1).trim();
    if (value.startsWith('"') && value.endsWith('"')) {
      value = value.slice(1, -1);
    }
    if (key === "title" || key === "description" || key === "date") {
      frontmatter[key] = value;
    }
  }

  return { frontmatter, body };
};

const markdownComponents = {
  h1: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h1 className="text-neutral-800 text-lg font-medium mt-6 mb-2" {...props}>
      {children}
    </h1>
  ),
  h2: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h2 className="text-neutral-800 text-lg font-medium mt-6 mb-2" {...props}>
      {children}
    </h2>
  ),
  h3: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h3 className="text-neutral-800 text-base font-medium mt-4 mb-2" {...props}>
      {children}
    </h3>
  ),
  p: ({ children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
    <p className="text-neutral-800 text-sm mt-2 leading-relaxed" {...props}>
      {children}
    </p>
  ),
  a: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a
      href={href}
      target={href?.startsWith("http") ? "_blank" : undefined}
      rel={href?.startsWith("http") ? "noopener noreferrer" : undefined}
      className="underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4"
      {...props}
    >
      {children}
    </a>
  ),
  ul: ({ children, ...props }: React.HTMLAttributes<HTMLUListElement>) => (
    <ul className="list-disc pl-4 mt-2 text-neutral-800 text-sm" {...props}>
      {children}
    </ul>
  ),
  ol: ({ children, ...props }: React.HTMLAttributes<HTMLOListElement>) => (
    <ol className="list-decimal pl-4 mt-2 text-neutral-800 text-sm" {...props}>
      {children}
    </ol>
  ),
  li: ({ children, ...props }: React.HTMLAttributes<HTMLLIElement>) => (
    <li className="mt-1" {...props}>
      {children}
    </li>
  ),
  blockquote: ({ children, ...props }: React.HTMLAttributes<HTMLQuoteElement>) => (
    <blockquote
      className="border-l-2 border-neutral-300 pl-3 italic text-neutral-600 mt-3"
      {...props}
    >
      {children}
    </blockquote>
  ),
  code: ({ children, className, ...props }: React.HTMLAttributes<HTMLElement>) => {
    const isInline = !className;
    return isInline ? (
      <code
        className="bg-neutral-100 rounded px-1 py-0.5 text-xs font-mono text-neutral-800"
        {...props}
      >
        {children}
      </code>
    ) : (
      <code
        className="bg-neutral-100 rounded px-1 py-0.5 text-xs font-mono text-neutral-800"
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children, ...props }: React.HTMLAttributes<HTMLPreElement>) => (
    <pre
      className="bg-neutral-100 rounded p-3 mt-2 overflow-x-auto text-xs font-mono"
      {...props}
    >
      {children}
    </pre>
  ),
  hr: (props: React.HTMLAttributes<HTMLHRElement>) => (
    <hr className="border-neutral-200 my-6" {...props} />
  ),
  table: ({ children, ...props }: React.TableHTMLAttributes<HTMLTableElement>) => (
    <table className="w-full text-sm text-left mt-2 border-collapse" {...props}>
      {children}
    </table>
  ),
  thead: ({ children, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) => (
    <thead className="border-b border-neutral-300" {...props}>
      {children}
    </thead>
  ),
  th: ({ children, ...props }: React.ThHTMLAttributes<HTMLTableCellElement>) => (
    <th className="py-1 pr-3 text-neutral-600 font-medium" {...props}>
      {children}
    </th>
  ),
  td: ({ children, ...props }: React.TdHTMLAttributes<HTMLTableCellElement>) => (
    <td className="py-1 pr-3 text-neutral-800" {...props}>
      {children}
    </td>
  ),
  tr: ({ children, ...props }: React.HTMLAttributes<HTMLTableRowElement>) => (
    <tr className="border-b border-neutral-100" {...props}>
      {children}
    </tr>
  ),
  sup: ({ children, ...props }: React.HTMLAttributes<HTMLElement>) => (
    <sup className="text-xs" {...props}>
      {children}
    </sup>
  ),
};

const JournalPage = () => {
  const { slug } = useParams<{ slug: string }>();
  const [content, setContent] = useState<string>("");
  const [frontmatter, setFrontmatter] = useState<Frontmatter>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const fetchJournal = async () => {
      try {
        const response = await fetch(`/journals/${slug}.md`);
        if (!response.ok) {
          throw new Error("Journal not found");
        }
        const text = await response.text();
        const { frontmatter: fm, body } = parseFrontmatter(text);
        setFrontmatter(fm);
        setContent(body);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load journal");
      } finally {
        setLoading(false);
      }
    };

    if (slug) {
      fetchJournal();
    }
  }, [slug]);

  if (loading) {
    return (
      <main className="bg-neutral-50 h-full min-h-screen pb-18">
        <section className="w-full max-w-xl mx-auto py-8">
          <p className="text-neutral-500 text-sm">Loading...</p>
        </section>
      </main>
    );
  }

  if (error) {
    return (
      <main className="bg-neutral-50 h-full min-h-screen pb-18">
        <section className="w-full max-w-xl mx-auto py-8">
          <Link
            to="/"
            className="text-neutral-500 text-sm underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4"
          >
            ← Back
          </Link>
          <p className="text-neutral-800 text-sm mt-4">{error}</p>
        </section>
      </main>
    );
  }

  return (
    <main className="bg-neutral-50 h-full min-h-screen pb-18">
      <section className="w-full max-w-xl mx-auto">
        <div className="py-8">
          <Link to="/">
            <img
              src="https://files.hisam.dev/pictures/pp_01.jpeg"
              className="size-8 rounded"
              alt="Hisam Fahri"
            />
          </Link>
        </div>

        <Link
          to="/"
          className="text-neutral-500 text-sm underline decoration-neutral-300 hover:decoration-neutral-800 underline-offset-4"
        >
          ← Back
        </Link>

        {frontmatter.title && (
          <h1 className="text-neutral-800 text-lg font-medium mt-4">
            {frontmatter.title}
          </h1>
        )}
        {frontmatter.date && (
          <p className="text-neutral-500 text-sm mt-1">{frontmatter.date}</p>
        )}
        {frontmatter.description && (
          <p className="text-neutral-500 text-sm mt-2 italic">
            {frontmatter.description}
          </p>
        )}

        <div className="mt-6">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {content}
          </ReactMarkdown>
        </div>
      </section>
    </main>
  );
};

export default JournalPage;
