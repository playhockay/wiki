import { TeamLogo } from "./team-logos";

const TEAMS: { id: string; slug: string; name: string }[] = [
	{ id: "anc", slug: "anchorage-auroras", name: "Anchorage Auroras" },
	{ id: "bus", slug: "busan-blizzards", name: "Busan Blizzards" },
	{ id: "dkr", slug: "dakar-djinns", name: "Dakar Djinns" },
	{ id: "gdl", slug: "guadalajara-gatos", name: "Guadalajara Gatos" },
	{ id: "hav", slug: "havana-hammers", name: "Havana Hammers" },
	{ id: "hel", slug: "helsinki-howlers", name: "Helsinki Howlers" },
	{ id: "jbg", slug: "johannesburg-jaguars", name: "Johannesburg Jaguars" },
	{ id: "mcm", slug: "mcmurdo-monoliths", name: "McMurdo Monoliths" },
	{ id: "mtl", slug: "montreal-maples", name: "Montréal Maples" },
	{ id: "mum", slug: "mumbai-monsoons", name: "Mumbai Monsoons" },
	{ id: "nrb", slug: "nairobi-narwhals", name: "Nairobi Narwhals" },
	{ id: "per", slug: "perth-pyres", name: "Perth Pyres" },
	{ id: "pra", slug: "prague-phantoms", name: "Prague Phantoms" },
	{ id: "rim", slug: "rimini-rinklers", name: "Rimini Rinklers" },
	{ id: "sao", slug: "sao-paulo-serpents", name: "São Paulo Serpents" },
	{ id: "sto", slug: "stockholm-sirens", name: "Stockholm Sirens" },
	{ id: "tok", slug: "tokyo-titans", name: "Tokyo Titans" },
	{ id: "ush", slug: "ushuaia-undertow", name: "Ushuaia Undertow" },
	{ id: "vla", slug: "vladivostok-vodkas", name: "Vladivostok Vodkas" },
	{ id: "wpg", slug: "winnipeg-wendigos", name: "Winnipeg Wendigos" },
];

export function TeamLogoGrid() {
	return (
		<div className="not-content grid grid-cols-4 sm:grid-cols-5 md:grid-cols-10 lg:grid-cols-20 gap-3 justify-items-center place-items-center md:justify-items-start">
			{TEAMS.map((team) => (
				<a
					key={team.id}
					href={`/teams/${team.slug}/`}
					className="group relative w-8 h-8"
					aria-label={team.name}
				>
					<TeamLogo
						teamId={team.id}
						variant="monochrome"
						className="w-8 h-8 absolute inset-0 opacity-40 transition-opacity group-hover:opacity-0"
					/>
					<TeamLogo
						teamId={team.id}
						variant="color"
						className="w-8 h-8 absolute inset-0 opacity-0 transition-opacity group-hover:opacity-100"
					/>
				</a>
			))}
		</div>
	);
}
