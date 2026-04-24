import { Parser } from "acorn";
import { visit } from "unist-util-visit";

/**
 * For each MDX file, if it references a JSX element whose name is a key in
 * `components`, inject the corresponding `import` statement at the top of the
 * file as an `mdxjsEsm` node. This lets Keystatic-produced MDX—which never
 * writes imports—still resolve our component library at render time.
 *
 * Keep the import paths relative and consistent with the content root depth
 * (all three collections sit at `src/content/docs/<collection>/`, three dirs
 * deep from `src/`).
 */

/** @type {Record<string, string>} */
const COMPONENTS = {
	Infobox: "import Infobox from '../../../components/mdx/Infobox.astro';",
};

export default function remarkInjectMdxComponents() {
	return (tree) => {
		const used = new Set();

		visit(tree, (node) => {
			if (
				(node.type === "mdxJsxFlowElement" || node.type === "mdxJsxTextElement") &&
				node.name &&
				Object.hasOwn(COMPONENTS, node.name)
			) {
				used.add(node.name);
			}
		});

		if (used.size === 0) return;

		// Strip any existing imports for the same components so we don't
		// double-declare (e.g. if an author hand-wrote the import).
		tree.children = tree.children.filter((child) => {
			if (child.type !== "mdxjsEsm") return true;
			for (const name of used) {
				if (new RegExp(`\\bimport\\s+${name}\\b`).test(child.value)) return false;
			}
			return true;
		});

		for (const name of used) {
			const code = COMPONENTS[name];
			const estree = Parser.parse(code, {
				sourceType: "module",
				ecmaVersion: "latest",
			});
			tree.children.unshift({
				type: "mdxjsEsm",
				value: code,
				data: { estree },
			});
		}
	};
}
