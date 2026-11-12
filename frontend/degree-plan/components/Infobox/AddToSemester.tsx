import React, { useContext, useEffect, useRef, useState } from "react";
import styled from "@emotion/styled";
import useSWR from "swr";
import { DegreePlan, Fulfillment } from "@/types";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { PlanSemestersContext } from "@/components/FourYearPlan/PlanSemestersContext";
import { translateSemester } from "@/components/FourYearPlan/Semester";
import ToastContext from "@/components/Toast/Toast";
import useAddToSemester from "@/hooks/useAddToSemester";

const Row = styled.div`
  position: relative;
  display: inline-flex;
  align-items: stretch;
  margin: 0.5rem 0 0.25rem;
`;

const MainButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 0.85rem;
  border: none;
  border-radius: 0.3rem 0 0 0.3rem;
  background: var(--primary-color-xx-dark);
  color: #fff;
  font-size: 0.9rem;
  font-weight: 700;
  line-height: 1.2;
  white-space: nowrap;
  cursor: pointer;

  &:hover:not(:disabled) {
    background: var(--primary-color-xxx-dark);
  }

  &:disabled {
    background: var(--green-color);
    cursor: default;
  }

  i {
    font-size: 0.8rem;
  }
`;

const MenuButton = styled.button`
  padding: 0 0.65rem;
  border: none;
  border-radius: 0 0.3rem 0.3rem 0;
  background: var(--primary-color-xxx-dark);
  color: #fff;
  font-size: 0.8rem;
  cursor: pointer;

  &:hover {
    background: var(--primary-color-ultra-dark);
  }
`;

const Menu = styled.div`
  position: absolute;
  top: calc(100% + 0.3rem);
  left: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  min-width: 11rem;
  max-height: 12rem;
  overflow-y: auto;
  padding: 0.25rem;
  background: #fff;
  border: 1px solid rgba(129, 154, 225, 0.35);
  border-radius: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
`;

const MenuItem = styled.button`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.65rem;
  border: none;
  border-radius: 5px;
  background: none;
  color: var(--primary-color-ultra-dark);
  font-size: 0.85rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;

  &:hover:not(:disabled) {
    background: var(--primary-color-light);
  }

  &:disabled {
    opacity: 0.55;
    cursor: default;
  }
`;

const Muted = styled.span`
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--primary-color-xxx-dark);
`;

/** The current semester if the plan has it, else the next one it has, else its last. */
const defaultSemester = (semesters: string[], current: string | undefined) => {
  const terms = semesters.filter(
    (semester) => semester !== TRANSFER_CREDIT_SEMESTER_KEY
  );
  if (current && terms.includes(current)) return current;
  return (
    terms.find((semester) => !current || semester > current) ??
    terms[terms.length - 1] ??
    semesters[0]
  );
};

interface AddToSemesterProps {
  fullCode: string;
  degreePlanId: DegreePlan["id"];
  currentSemester?: string;
  onAdded: () => void;
}

const AddToSemester = ({
  fullCode,
  degreePlanId,
  currentSemester,
  onAdded,
}: AddToSemesterProps) => {
  const { semesters } = useContext(PlanSemestersContext);
  const showToast = useContext(ToastContext);
  const addToSemester = useAddToSemester(degreePlanId);
  const { data: fulfillments } = useSWR<Fulfillment[]>(
    `/api/degree/degreeplans/${degreePlanId}/fulfillments`
  );
  const [menuOpen, setMenuOpen] = useState(false);
  const rowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menuOpen) return undefined;
    const close = (e: MouseEvent) => {
      if (!rowRef.current?.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [menuOpen]);

  if (!semesters.length) return null;

  const existing = fulfillments?.find(
    (fulfillment) => fulfillment.full_code === fullCode
  );
  const placedIn = existing?.semester ?? null;
  const target = defaultSemester(semesters, currentSemester);
  const code = fullCode.replace("-", " ");

  const add = async (semester: string) => {
    setMenuOpen(false);
    if (!(await addToSemester(fullCode, semester, { inPlan: !!existing }))) return;
    showToast(
      `${existing ? "Moved" : "Added"} ${code} to ${translateSemester(
        semester
      )}`,
      false
    );
    onAdded();
  };

  return (
    <Row ref={rowRef}>
      <MainButton
        type="button"
        disabled={placedIn === target}
        onClick={() => add(target)}
      >
        <i
          className={`fas ${placedIn === target ? "fa-check" : "fa-plus"}`}
          aria-hidden
        />
        {placedIn === target
          ? `In ${translateSemester(target)}`
          : `${existing ? "Move" : "Add"} to ${translateSemester(target)}`}
      </MainButton>
      <MenuButton
        type="button"
        aria-label="Choose semester"
        aria-haspopup="listbox"
        aria-expanded={menuOpen}
        onClick={() => setMenuOpen(!menuOpen)}
      >
        <i className="fas fa-chevron-down" aria-hidden />
      </MenuButton>
      {menuOpen && (
        <Menu role="listbox">
          {semesters.map((semester) => (
            <MenuItem
              key={semester}
              type="button"
              role="option"
              aria-selected={semester === placedIn}
              disabled={semester === placedIn}
              onClick={() => add(semester)}
            >
              <span>{translateSemester(semester)}</span>
              {semester === placedIn && <Muted>Added</Muted>}
            </MenuItem>
          ))}
        </Menu>
      )}
    </Row>
  );
};

export default AddToSemester;
