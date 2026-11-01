import React, { useContext, useEffect, useRef, useState } from "react";
import styled from "@emotion/styled";
import { useDrag } from "react-dnd";
import { useSWRConfig } from "swr";
import { GeneratedPlacement } from "@/types";
import { postFetcher } from "@/hooks/swrcrud";
import { ItemTypes } from "@/components/Dock/dnd/constants";
import { SearchPanelContext } from "../Search/SearchPanel";
import { CuLabel } from "../Course/Course";
import RequirementJump from "../Requirements/RequirementJump";
import { ghostDomId } from "@/hooks/requirementNav";
import { scheduleCardTitle } from "@/utils/scheduleLabel";
import { ClaimBar, useProgramClaims } from "./programColor";

const Card = styled.div<{ $dashed?: boolean; $dragging?: boolean; $frozen?: boolean }>`
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.65rem;
  position: relative;
  overflow: hidden;
  width: 100%;
  min-height: 28px;
  margin-top: 0.5rem;
  padding: 0.35rem 0.65rem;
  border-radius: 9px;
  background: ${(props) =>
    props.$frozen ? "rgba(217, 119, 6, 0.12)" : "var(--background-grey)"};
  border-width: 1px;
  border-style: ${(props) => (props.$dashed && !props.$frozen ? "dashed" : "solid")};
  border-color: ${(props) =>
    props.$frozen ? "#d97706" : props.$dashed ? "rgba(0, 0, 0, 0.32)" : "transparent"};
  box-shadow: rgba(0, 0, 0, 0.01) 0px 6px 5px 0px, rgba(0, 0, 0, 0.04) 0px 0px 0px 1px;
  font-size: var(--type-body);
  font-weight: 600;
  color: ${(props) => (props.$frozen ? "#b45309" : "inherit")};
  text-wrap: nowrap;
  cursor: grab;
  opacity: ${(props) => (props.$dragging ? 0.5 : 1)};
  transition: border-color 0.15s ease, transform 0.15s ease;

  &:hover {
    border-color: ${(props) =>
      props.$frozen ? "#d97706" : props.$dashed ? "rgba(0, 0, 0, 0.55)" : "#6274f1"};
    transform: translateX(2px);
  }
`;

const Title = styled.div`
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: left;
`;

const Quiet = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  border: 1px solid rgba(98, 116, 241, 0.35);
  background: rgba(98, 116, 241, 0.08);
  color: #3d4ed8;
  font: inherit;
  font-size: var(--type-body);
  font-weight: 600;
  line-height: 1;
  cursor: pointer;
  padding: 1px 5px;
  border-radius: 3px;
  flex-shrink: 0;
`;

const Popup = styled.div`
  position: fixed;
  z-index: 10000;
  min-width: 9rem;
  max-height: 16rem;
  overflow-y: auto;
  padding: 4px;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
`;

const OptionButton = styled.button`
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  border-radius: 4px;
  padding: 6px 8px;
  font: inherit;
  font-size: var(--type-body);
  font-weight: 600;
  cursor: pointer;

  &:hover {
    background: rgba(217, 119, 6, 0.12);
  }
`;

interface GhostCourseProps {
  placement: GeneratedPlacement;
  planId: number;
  /** Dragged onto this semester, so the suggestion stays here. */
  frozen?: boolean;
  /** Clear that pin. The requirement stays on the plan. */
  onUnpin?: () => void;
}

type OpenListener = (id: string | null) => void;
const openListeners = new Set<OpenListener>();
let openOptionsId: string | null = null;

const publishOpenOptions = (id: string | null) => {
  openOptionsId = id;
  openListeners.forEach((listener) => listener(id));
};

const GhostCourse = ({ placement, planId, frozen = false, onUnpin }: GhostCourseProps) => {
  const programs = useProgramClaims(planId);
  const claimKeys = programs.claimsForRules(placement.rules || []);
  if (placement.component_key && !claimKeys.includes(placement.component_key)) {
    claimKeys.push(placement.component_key);
  }
  const claimBar = (
    <ClaimBar keys={claimKeys} order={programs.order} titles={programs.titles} />
  );
  const { mutate } = useSWRConfig();
  const { setSearchPanelOpen, setSearchRuleId, setSearchRuleQuery } = useContext(SearchPanelContext);
  const instanceId = placement.slot_ids.join(",") || placement.full_code || placement.label;
  const [openOptions, setOpenOptions] = useState(false);
  const [popupAt, setPopupAt] = useState<{ top: number; left: number } | null>(null);
  const popupRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const listener: OpenListener = (id) => setOpenOptions(id === instanceId);
    openListeners.add(listener);
    setOpenOptions(openOptionsId === instanceId);
    return () => {
      openListeners.delete(listener);
      if (openOptionsId === instanceId) publishOpenOptions(null);
    };
  }, [instanceId]);
  const fulfillmentsKey = `/api/degree/degreeplans/${planId}/fulfillments`;

  const [{ isDragging }, drag] = useDrag(
    () => ({
      type: ItemTypes.GHOST,
      item: {
        full_code: placement.full_code,
        kind: placement.kind,
        rules: placement.rules,
        slot_ids: placement.slot_ids,
        semester: placement.semester,
        rule_id: placement.rules[0] ?? -1,
      },
      collect: (monitor) => ({ isDragging: !!monitor.isDragging() }),
    }),
    [placement]
  );

  const accept = async (fullCode: string, semester = placement.semester) => {
    await postFetcher(fulfillmentsKey, {
      full_code: fullCode,
      semester,
      rules: placement.rules,
    });
    mutate(fulfillmentsKey);
  };

  const acceptPlacement = async () => {
    if (!placement.full_code) return;
    await postFetcher(fulfillmentsKey, {
      full_code: placement.full_code,
      semester: placement.semester,
    });
    mutate(fulfillmentsKey);
  };

  const openSearch = () => {
    const ruleId = placement.rules[0];
    if (ruleId == null) return;
    setSearchRuleId(ruleId);
    setSearchRuleQuery(placement.rule_q);
    setSearchPanelOpen(true);
  };

  const code = (value: string) => value.replace(/-/g, " ");
  const slotName = scheduleCardTitle(placement);
  const options = [
    ...(placement.full_code ? [placement.full_code] : []),
    ...placement.alternatives.filter((alt) => alt !== placement.full_code),
  ];

  useEffect(() => {
    if (!openOptions) return undefined;
    const close = (event: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(event.target as Node)) {
        publishOpenOptions(null);
      }
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [openOptions]);

  const togglePopup = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    if (openOptions) {
      publishOpenOptions(null);
      return;
    }
    const rect = event.currentTarget.getBoundingClientRect();
    setPopupAt({ top: rect.bottom + 4, left: Math.max(8, rect.right - 160) });
    publishOpenOptions(instanceId);
  };

  const choose = async (fullCode: string) => {
    publishOpenOptions(null);
    await accept(fullCode);
  };

  const units = <CuLabel className="course-cu">{Number(placement.cu).toFixed(1)} CU</CuLabel>;
  const showMenu = placement.overlap ? options.length > 0 : options.length >= 2;
  const optionsButton = showMenu && (
    <Quiet
      type="button"
      onMouseDown={(event) => event.stopPropagation()}
      onClick={togglePopup}
      aria-expanded={openOptions}
      aria-label={`${options.length} options`}
    >
      {options.length}
      <span aria-hidden="true">{openOptions ? "▴" : "▾"}</span>
    </Quiet>
  );
  const optionsPopup = openOptions && popupAt && (
    <Popup ref={popupRef} style={{ top: popupAt.top, left: popupAt.left }}>
      {options.map((option) => (
        <OptionButton key={option} type="button" onClick={() => choose(option)}>
          {code(option)}
        </OptionButton>
      ))}
    </Popup>
  );
  const unpin = frozen && onUnpin ? (
    <Quiet
      type="button"
      aria-label="Unpin requirement"
      title="Unpin. The requirement stays, and can move again."
      onMouseDown={(event) => event.stopPropagation()}
      onClick={(event) => {
        event.stopPropagation();
        onUnpin();
      }}
    >
      <i className="fa fa-times" aria-hidden="true" />
    </Quiet>
  ) : null;
  const jump = (
    <RequirementJump
      ruleIds={placement.rules}
      cycleKey={placement.slot_ids[0] || placement.full_code || placement.kind}
    />
  );

  if (placement.kind === "placeholder") {
    return (
      <>
        <Card id={ghostDomId(placement)} ref={drag} $dashed $frozen={frozen} $dragging={isDragging} onClick={options.length > 1 ? undefined : openSearch}>
          {claimBar}
          <Title>{slotName}</Title>
          {jump}
          {optionsButton}
          {unpin}
          {units}
        </Card>
        {optionsPopup}
      </>
    );
  }

  if (placement.kind === "placement" && placement.full_code) {
    return (
      <Card id={ghostDomId(placement)} ref={drag} $frozen={frozen} $dragging={isDragging}>
        {claimBar}
        <Title>{code(placement.full_code)}</Title>
        {jump}
        <Quiet type="button" onClick={(event) => { event.stopPropagation(); acceptPlacement(); }}>Add</Quiet>
        {units}
      </Card>
    );
  }

  return (
    <div>
      <Card id={ghostDomId(placement)} ref={drag} $dashed $frozen={frozen} $dragging={isDragging}>
        {claimBar}
        <Title>{slotName}</Title>
        {jump}
        {optionsButton}
        {unpin}
        {units}
      </Card>
      {optionsPopup}
    </div>
  );
};

export default GhostCourse;
