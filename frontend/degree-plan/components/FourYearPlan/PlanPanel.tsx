import SelectListDropdown from "./SelectListDropdown";
import Semesters from "./Semesters";
import styled from "@emotion/styled";
import type { DegreePlan } from "@/types";
import React, { useContext, useEffect, useState } from "react";
import { useSWRCrud } from '@/hooks/swrcrud';
import { postFetcher } from "@/hooks/swrcrud";
import { useSWRConfig } from "swr";
import { EditButton } from './EditButton';
import { PanelTopBarButton, PanelTopBarIcon } from "./PanelCommon";
import { PanelContainer, PanelHeader, PanelTopBarIconList, PanelBody } from "./PanelCommon";
import { ModalKey } from "./DegreeModal";
import {
  emptyGenConfig,
  genConfigKey,
  parseGenConfig,
  StoredGenConfig,
} from "@/hooks/generateConfig";
import { useGenerateSchedule } from "@/hooks/useGenerateSchedule";
import ToastContext from "../Toast/Toast";

const ShowStatsText = styled.div`
    min-width: 6rem;
`

const CompactButton = styled.button<{ $on?: boolean }>`
    border: 1px solid rgba(32, 64, 128, 0.18);
    background: ${(props) => (props.$on ? "rgba(255, 255, 255, 0.72)" : "transparent")};
    color: var(--primary-color-xxx-dark);
    border-radius: 999px;
    padding: 0.2rem 0.7rem;
    font: inherit;
    font-size: var(--type-body);
    font-weight: 600;
    line-height: 1.2;
    cursor: pointer;
    white-space: nowrap;
`;

const ShowStatsButton = ({ showStats, setShowStats }: { showStats: boolean, setShowStats: (arg0: boolean) => void }) => (
    <PanelTopBarButton onClick={() => setShowStats(!showStats)}>
        <PanelTopBarIcon>
            <i className={`fas fa-md fa-chart-bar ${showStats ? "" : "icon-crossed-out"}`}/>
        </PanelTopBarIcon>
        <ShowStatsText>
            {showStats ? "Hide Stats" : "Show Stats"}
        </ShowStatsText>
    </PanelTopBarButton>
);

interface PlanPanelProps {
    setModalKey: (arg0: ModalKey) => void;
    modalKey: string | null;
    setModalObject: (arg0: DegreePlan | null) => void;
    setActiveDegreeplan: (arg0: DegreePlan | null) => void;
    activeDegreeplan: DegreePlan | null;
    degreeplans: DegreePlan[] | undefined;
    isLoading: boolean;
    currentSemester?: string;
    setShowOnboardingModal: (arg0: boolean) => void;
}

const PlanPanel = ({ 
    setModalKey,
    modalKey,
    setModalObject,
    setActiveDegreeplan,
    setShowOnboardingModal,
    activeDegreeplan,
    degreeplans,
    isLoading,
    currentSemester,
} : PlanPanelProps) => {
    

    const { copy: copyDegreeplan } = useSWRCrud<DegreePlan>('/api/degree/degreeplans');
    const [showStats, setShowStats] = useState(false);
    const [editMode, setEditMode] = useState(false);
    const [genConfig, setGenConfig] = useState<StoredGenConfig | null>(null);
    const [semesterKeys, setSemesterKeys] = useState<string[]>([]);
    const showToast = useContext(ToastContext);
    const { mutate } = useSWRConfig();
    const { proposal, error } = useGenerateSchedule(
        activeDegreeplan?.id,
        genConfig,
        semesterKeys,
    );

    useEffect(() => {
        if (!activeDegreeplan || typeof window === "undefined") return;
        setGenConfig(parseGenConfig(localStorage.getItem(genConfigKey(activeDegreeplan.id))));
    }, [activeDegreeplan?.id]);

    useEffect(() => {
        if (!activeDegreeplan || !genConfig || typeof window === "undefined") return;
        localStorage.setItem(genConfigKey(activeDegreeplan.id), JSON.stringify(genConfig));
    }, [genConfig, activeDegreeplan?.id]);

    useEffect(() => {
        if (error) showToast(error, true);
    }, [error]);

    useEffect(() => {
        const notes = (proposal?.violations || []).filter((row) => row.kind === "also_offered" && row.message);
        notes.forEach((row) => showToast(row.message as string, true));
    }, [proposal]);

    useEffect(() => {
        const count = proposal?.unplaced?.length || 0;
        if (!count) return undefined;
        // A short semester list can fail the first pass. The next pass adds those
        // columns and places the courses, so wait before reporting a real miss.
        const handle = window.setTimeout(() => {
            showToast(
                count === 1 ? "1 course could not be placed" : `${count} courses could not be placed`,
                true,
            );
        }, 1500);
        return () => window.clearTimeout(handle);
    }, [proposal]);

    const acceptAll = async () => {
        if (!activeDegreeplan || !proposal) return;
        const courses = proposal.placements.filter((row) => row.kind === "course" && row.full_code);
        for (const row of courses) {
            await postFetcher(`/api/degree/degreeplans/${activeDegreeplan.id}/fulfillments`, {
                full_code: row.full_code,
                semester: row.semester,
                rules: row.rules,
            });
        }
        mutate(`/api/degree/degreeplans/${activeDegreeplan.id}/fulfillments`);
    };

    const setSemesterGen = (semester: string, next: { cuCap: number; gap: boolean }) => {
        setGenConfig((current) => {
            const base = current || emptyGenConfig();
            return { ...base, semesters: { ...base.semesters, [semester]: next } };
        });
    };

    const pinSlot = (slotId: string, semester: string) => {
        setGenConfig((current) => {
            const base = current || emptyGenConfig();
            return { ...base, pinnedSlots: { ...(base.pinnedSlots || {}), [slotId]: semester } };
        });
    };

    const unpinSlot = (slotId: string) => {
        setGenConfig((current) => {
            const base = current || emptyGenConfig();
            const pinnedSlots = { ...(base.pinnedSlots || {}) };
            delete pinnedSlots[slotId];
            return { ...base, pinnedSlots };
        });
    };

    return (
            <PanelContainer>
                <PanelHeader>
                    <SelectListDropdown
                        itemType="degree plan" 
                        active={activeDegreeplan || undefined}
                        getItemName={(item: DegreePlan) => item.name}
                        allItems={degreeplans || []} 
                        selectItem={(id: DegreePlan["id"]) => setActiveDegreeplan(degreeplans?.filter(d => d.id === id)[0] || null)}
                        mutators={{
                            copy: (item: DegreePlan) => {
                                (copyDegreeplan({...item, name: `${item.name} (copy)`}, item.id) as Promise<any>)
                                .then((copied) => copied && setActiveDegreeplan(copied))
                            },
                            remove: (item: DegreePlan) => {
                                setModalKey("plan-remove")
                                setModalObject(item)
                            },
                            rename: (item: DegreePlan) => {
                                setModalKey("plan-rename")
                                setModalObject(item)
                            },
                            create: () => {
                                setShowOnboardingModal(true);
                            }
                        }}
                        isLoading={isLoading} 
                    />
                    <PanelTopBarIconList>
                        <CompactButton $on={showStats} onClick={() => setShowStats(!showStats)}>
                            {showStats ? "Stats" : "Stats off"}
                        </CompactButton>
                        <CompactButton $on={Boolean(genConfig?.allowSummer)} onClick={() => setGenConfig((current) => {
                            const base = current || emptyGenConfig();
                            return { ...base, allowSummer: !base.allowSummer };
                        })}>
                            {genConfig?.allowSummer ? "Summer" : "No summer"}
                        </CompactButton>
                        {proposal && proposal.placements.some((row) => row.kind === "course") && (
                            <CompactButton $on onClick={acceptAll}>
                                Accept courses
                            </CompactButton>
                        )}
                        <EditButton editMode={editMode} setEditMode={setEditMode} />
                    </PanelTopBarIconList>
                </PanelHeader>
                {/** map to semesters */}
                <PanelBody>
                    <Semesters 
                    activeDegreeplan={activeDegreeplan || undefined} 
                    showStats={showStats}
                    editMode={editMode}
                    setEditMode={setEditMode}
                    setModalKey={setModalKey}
                    setModalObject={setModalObject}
                    isLoading={isLoading}
                    currentSemester={currentSemester}
                    ghosts={proposal?.placements || []}
                    genBySemester={genConfig?.semesters}
                    onGenConfig={setSemesterGen}
                    onSemesterKeys={setSemesterKeys}
                    syntheticKeys={(proposal?.semesters || []).map((row) => row.key)}
                    onPinSlot={pinSlot}
                    onUnpinSlot={unpinSlot}
                    pinnedSlots={genConfig?.pinnedSlots}
                    showSummer={Boolean(genConfig?.allowSummer)}
                    />
                </PanelBody>
            </PanelContainer>
    );
}

export default PlanPanel;
