import { collection, config, fields } from "@keystatic/core";
import { block } from "@keystatic/core/content-components";

const tagField = fields.array(fields.text({ label: "Tag" }), {
	label: "Tags",
	itemLabel: (props) => props.value,
});

const infoboxBlock = block({
	label: "Infobox",
	description: "A callout with a variant color and optional title.",
	schema: {
		variant: fields.select({
			label: "Variant",
			options: [
				{ label: "Neutral", value: "neutral" },
				{ label: "Ice (blue)", value: "ice" },
				{ label: "Jambono (gold)", value: "jambono" },
				{ label: "Sixth (purple)", value: "sixth" },
				{ label: "Positive (green)", value: "positive" },
				{ label: "Negative (red)", value: "negative" },
			],
			defaultValue: "neutral",
		}),
		title: fields.text({ label: "Title (optional)" }),
	},
});

function docCollection(name: string, label: string, slug: string) {
	return collection({
		label,
		slugField: "title",
		path: `src/content/docs/${slug}/*`,
		format: { contentField: "content" },
		entryLayout: "content",
		columns: ["title", "lastUpdated"],
		schema: {
			title: fields.slug({ name: { label: "Title" } }),
			description: fields.text({
				label: "Description",
				description: "Short summary shown in search results and meta tags.",
				multiline: true,
			}),
			tags: tagField,
			lastUpdated: fields.date({
				label: "Last updated",
				defaultValue: { kind: "today" },
			}),
			content: fields.mdx({
				label: "Body",
				components: {
					Infobox: infoboxBlock,
				},
				options: {
					image: {
						directory: `src/assets/${slug}`,
						publicPath: `../../../assets/${slug}/`,
					},
				},
			}),
		},
	});
}

export default config({
	storage:
		process.env.NODE_ENV === "development"
			? { kind: "local" }
			: { kind: "github", repo: "playhockay/wiki" },
	ui: {
		brand: { name: "Hockay Wiki" },
	},
	collections: {
		guides: docCollection("guides", "Guides", "guides"),
		lore: docCollection("lore", "Lore", "lore"),
		teams: docCollection("teams", "Teams", "teams"),
		modifiers: docCollection("modifiers", "Modifiers", "modifiers"),
		glossary: docCollection("glossary", "Glossary", "glossary"),
	},
});
