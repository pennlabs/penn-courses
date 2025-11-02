import { Fulfillment } from "@/types";
import {
  createContext,
  MutableRefObject,
  PropsWithChildren,
  useContext,
  useRef,
} from "react";

export interface ExpandedCoursesPanelContextType {
  position: { top?: number; bottom?: number; left?: number; right?: number };
  setPosition: (arg0: ExpandedCoursesPanelContextType["position"]) => void;
  courses: Fulfillment[] | null | undefined;
  setCourses: (arg0: Fulfillment[] | null | undefined) => void;
  retract: () => void;
  set_retract: (arg0: () => void) => void;
  open: boolean;
  setOpen: (arg0: boolean) => void;
  ruleId: number | null;
  setRuleId: (arg0: number | null) => void;
  searchRef: MutableRefObject<any> | null;
  setSearchRef: (arg0: MutableRefObject<any> | null) => void;
  degreePlanId: number | undefined;
}

export const ExpandedCoursesPanelContext = createContext<
  ExpandedCoursesPanelContextType
>({
  position: { top: 0, left: 0 },
  setPosition: (arg0) => {}, // placeholder
  courses: null,
  setCourses: (courses) => {}, // placeholder
  retract: () => {}, // placehoder
  set_retract: (arg0) => {}, // placeholder
  open: false,
  setOpen: (arg0) => {}, // placeholder
  ruleId: null,
  setRuleId: (arg0) => {},
  searchRef: null,
  setSearchRef: (arg0) => {},
  degreePlanId: undefined,
});

export const ExpandedCoursesPanelTrigger = ({
  courses,
  triggerType,
  changeExpandIcon,
  ruleId,
  searchRef,
  children,
}: PropsWithChildren<{
  courses: Fulfillment[];
  triggerType: "click" | "hover" | undefined;
  changeExpandIcon: () => void;
  ruleId: number;
  searchRef: MutableRefObject<any>;
}>) => {
  const ref = useRef<HTMLDivElement>(null);
  const {
    setPosition,
    setCourses,
    retract,
    set_retract,
    open,
    setOpen,
    setRuleId,
    setSearchRef,
  } = useContext(ExpandedCoursesPanelContext);

  const showExpandedCourses = () => {
    if (open) {
      setCourses(null);
      setOpen(false);
      setRuleId(null);
      retract();
    } else {
      setOpen(!open);
      setCourses(courses);
      set_retract(() => changeExpandIcon);
      setRuleId(ruleId);
      setSearchRef(searchRef);
      if (!ref.current) return;
      const position: ExpandedCoursesPanelContextType["position"] = {};
      const {
        left,
        top,
        right,
        bottom,
      } = searchRef.current.getBoundingClientRect();

      // calculate the optimal position
      let vw = Math.max(
        document.documentElement.clientWidth || 0,
        window.innerWidth || 0
      );
      let vh = Math.max(
        document.documentElement.clientHeight || 0,
        window.innerHeight || 0
      );
      if (left > vw - right) position["right"] = vw - left + 5;
      // set the right edge of the ExpandedCourses panel to left edge of trigger
      else position["left"] = right - 5;
      if (top > vh - bottom) position["bottom"] = vh - bottom;
      else position["top"] = top;

      setPosition(position);
    }
  };

  return (
    <div
      ref={ref}
      onClick={showExpandedCourses}
      className="review-panel-trigger"
    >
      {children}
    </div>
  );
};
