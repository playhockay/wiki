import { AncColorLogo, AncMonochromeLogo } from "./anc";
import { BusColorLogo, BusMonochromeLogo } from "./bus";
import { DkrColorLogo, DkrMonochromeLogo } from "./dkr";
import { GdlColorLogo, GdlMonochromeLogo } from "./gdl";
import { HavColorLogo, HavMonochromeLogo } from "./hav";
import { HelColorLogo, HelMonochromeLogo } from "./hel";
import { JbgColorLogo, JbgMonochromeLogo } from "./jbg";
import { McmColorLogo, McmMonochromeLogo } from "./mcm";
import { MtlColorLogo, MtlMonochromeLogo } from "./mtl";
import { MumColorLogo, MumMonochromeLogo } from "./mum";
import { NrbColorLogo, NrbMonochromeLogo } from "./nrb";
import { PerColorLogo, PerMonochromeLogo } from "./per";
import { PraColorLogo, PraMonochromeLogo } from "./pra";
import { RimColorLogo, RimMonochromeLogo } from "./rim";
import { SaoColorLogo, SaoMonochromeLogo } from "./sao";
import { StoColorLogo, StoMonochromeLogo } from "./sto";
import { TokColorLogo, TokMonochromeLogo } from "./tok";
import { UshColorLogo, UshMonochromeLogo } from "./ush";
import { VlaColorLogo, VlaMonochromeLogo } from "./vla";
import { WpgColorLogo, WpgMonochromeLogo } from "./wpg";

type LogoComponent = React.ComponentType<{ className?: string }>;

const LOGOS: Record<string, Record<"color" | "monochrome", LogoComponent>> = {
	anc: { color: AncColorLogo, monochrome: AncMonochromeLogo },
	bus: { color: BusColorLogo, monochrome: BusMonochromeLogo },
	dkr: { color: DkrColorLogo, monochrome: DkrMonochromeLogo },
	gdl: { color: GdlColorLogo, monochrome: GdlMonochromeLogo },
	hav: { color: HavColorLogo, monochrome: HavMonochromeLogo },
	hel: { color: HelColorLogo, monochrome: HelMonochromeLogo },
	jbg: { color: JbgColorLogo, monochrome: JbgMonochromeLogo },
	mcm: { color: McmColorLogo, monochrome: McmMonochromeLogo },
	mtl: { color: MtlColorLogo, monochrome: MtlMonochromeLogo },
	mum: { color: MumColorLogo, monochrome: MumMonochromeLogo },
	nrb: { color: NrbColorLogo, monochrome: NrbMonochromeLogo },
	per: { color: PerColorLogo, monochrome: PerMonochromeLogo },
	pra: { color: PraColorLogo, monochrome: PraMonochromeLogo },
	rim: { color: RimColorLogo, monochrome: RimMonochromeLogo },
	sao: { color: SaoColorLogo, monochrome: SaoMonochromeLogo },
	sto: { color: StoColorLogo, monochrome: StoMonochromeLogo },
	tok: { color: TokColorLogo, monochrome: TokMonochromeLogo },
	ush: { color: UshColorLogo, monochrome: UshMonochromeLogo },
	vla: { color: VlaColorLogo, monochrome: VlaMonochromeLogo },
	wpg: { color: WpgColorLogo, monochrome: WpgMonochromeLogo },
};

export function TeamLogo({
	teamId,
	variant = "color",
	className,
}: {
	teamId: string;
	variant?: "color" | "monochrome";
	className?: string;
}) {
	const Logo = LOGOS[teamId]?.[variant];
	if (!Logo) return null;
	return <Logo className={className} />;
}
