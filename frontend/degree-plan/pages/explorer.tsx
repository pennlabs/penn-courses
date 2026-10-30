import dynamic from "next/dynamic";
import Head from "next/head";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";
import styled from "@emotion/styled";
import Select from "react-select";
import useSWR from "swr";
import type { DegreeListing, DegreePlan, Fulfillment } from "@/types";
import {
  componentLabel,
  degreeLabel,
  ENDPOINTS,
  parseProgramKeys,
  planPrograms,
  programKey,
  toProgram,
  type MajorListing,
  type MinorListing,
  type Program,
  type ProgramRef,
} from "@/components/Explorer/programs";
import { normalizeFullCode, type CourseDetail } from "@/components/Explorer/matcher";

// React Flow and elkjs measure the DOM, so render the graph on the client only.
const DegreeExplorer = dynamic(() => import("@/components/Explorer/DegreeExplorer"), {
  ssr: false,
});

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    const error = new Error(`Request to ${url} failed with status ${res.status}`) as Error & {
      status: number;
    };
    error.status = res.status;
    throw error;
  }
  return res.json();
};

const Page = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f6f8fa;
`;

const Header = styled.header`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid #d0d4da;
  background: #fff;
  h1 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
    white-space: nowrap;
  }
`;

const CourseSearch = styled.form`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #57606a;
  input {
    width: 9rem;
    padding: 0.45rem 0.6rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.85rem;
  }
`;

const Message = styled.div`
  margin: auto;
  color: #57606a;
`;

const errorMessage = (error: { status?: number }) =>
  error.status === 401 || error.status === 403
    ? "Log in to Penn Degree Plan (with beta access) to use the explorer."
    : "Couldn't load programs. Is the backend running?";

interface ProgramOption extends ProgramRef {
  value: string;
  label: string;
}

const option = (ref: ProgramRef, label: string): ProgramOption => ({
  ...ref,
  value: programKey(ref),
  label,
});

/**
 * Internal tool for viewing how programs' rules fit together. Not linked from the app.
 * Pick any mix of degrees, majors and minors, e.g. two degrees from different schools.
 * Or open one of your degree plans to see its programs, with every course on the trees.
 * Search a course to highlight every requirement it can count toward.
 * The selection is kept in the URL (?programs=degree-3,major-12&course=CIS-1200, or
 * ?plan=5) so a view can be shared.
 */
export default function ExplorerPage() {
  const router = useRouter();
  const refs = parseProgramKeys(router.query.programs);
  const selectedKeys = refs.map(programKey).join(",");
  const planId = typeof router.query.plan === "string" ? router.query.plan : "";
  const courseCode = typeof router.query.course === "string" ? router.query.course : "";
  const [courseInput, setCourseInput] = useState(courseCode);
  useEffect(() => setCourseInput(courseCode), [courseCode]);

  const setQuery = (changes: Record<string, string>) => {
    const query = { ...router.query, ...changes };
    Object.keys(query).forEach((key) => !query[key] && delete query[key]);
    router.push({ query }, undefined, { shallow: true });
  };

  const { data: degrees, error: degreesError } = useSWR<DegreeListing[]>(
    ENDPOINTS.degree,
    fetcher
  );
  const { data: majors, error: majorsError } = useSWR<MajorListing[]>(ENDPOINTS.major, fetcher);
  const { data: minors, error: minorsError } = useSWR<MinorListing[]>(ENDPOINTS.minor, fetcher);

  // Only the logged-in user's own plans.
  const { data: plans, error: plansError } = useSWR<Pick<DegreePlan, "id" | "name">[]>(
    "/api/degree/degreeplans",
    fetcher
  );
  const { data: plan, error: planError } = useSWR<DegreePlan>(
    planId ? `/api/degree/degreeplans/${planId}` : null,
    fetcher
  );
  const { data: fulfillments, error: fulfillmentsError } = useSWR<Fulfillment[]>(
    planId ? `/api/degree/degreeplans/${planId}/fulfillments` : null,
    fetcher
  );
  const planView = useMemo(
    () =>
      plan && fulfillments
        ? { programs: planPrograms(plan), overlay: { name: plan.name, fulfillments } }
        : null,
    [plan, fulfillments]
  );

  const { data: pickedPrograms, error: programsError } = useSWR<Program[]>(
    selectedKeys && !planId ? `explorer-programs:${selectedKeys}` : null,
    () =>
      Promise.all(
        refs.map(async (ref) => toProgram(ref, await fetcher(`${ENDPOINTS[ref.kind]}/${ref.id}`)))
      ),
    // Keep showing the current trees while a changed selection loads.
    { keepPreviousData: true }
  );

  const { data: course, error: courseError } = useSWR<CourseDetail>(
    courseCode ? `/api/base/all/courses/${courseCode}` : null,
    fetcher
  );

  const groups = [
    {
      label: "Degrees",
      options: (degrees ?? []).map((d) => option({ kind: "degree", id: d.id }, degreeLabel(d))),
    },
    {
      label: "Majors",
      options: (majors ?? []).map((m) => option({ kind: "major", id: m.id }, componentLabel(m))),
    },
    {
      label: "Minors",
      options: (minors ?? []).map((m) => option({ kind: "minor", id: m.id }, componentLabel(m))),
    },
  ];
  const allOptions = groups.flatMap((group) => group.options);
  const loadingLists = !degrees || !majors || !minors;
  const error =
    degreesError ??
    majorsError ??
    minorsError ??
    plansError ??
    (planId ? planError ?? fulfillmentsError : programsError);
  const programs = planId ? planView?.programs : pickedPrograms;
  const planOptions = (plans ?? []).map((p) => ({ value: String(p.id), label: p.name }));

  return (
    <Page>
      <Head>
        <title>Degree Explorer</title>
      </Head>
      <Header>
        <h1>Degree Explorer</h1>
        <div style={{ width: 220 }}>
          <Select
            instanceId="plan-select"
            isClearable
            placeholder={plans ? "Open a degree plan..." : "Loading plans..."}
            options={planOptions}
            styles={{ menu: (base) => ({ ...base, zIndex: 10 }) }}
            value={planOptions.find((o) => o.value === planId) ?? null}
            onChange={(selected) => setQuery({ plan: selected?.value ?? "" })}
          />
        </div>
        <div style={{ flex: 1, maxWidth: 720 }}>
          <Select
            instanceId="program-select"
            isMulti
            isDisabled={!!planId}
            placeholder={
              planId
                ? "Programs come from the degree plan"
                : loadingLists
                ? "Loading programs..."
                : "Pick degrees, majors or minors..."
            }
            options={groups}
            // Above the canvas toolbar and React Flow's panels, which sit at z-index 5
            styles={{ menu: (base) => ({ ...base, zIndex: 10 }) }}
            value={
              planId
                ? []
                : refs
                    .map((ref) => allOptions.find((o) => o.value === programKey(ref)))
                    .filter((o): o is ProgramOption => o !== undefined)
            }
            onChange={(selected) => setQuery({ programs: selected.map((o) => o.value).join(",") })}
          />
        </div>
        <CourseSearch
          onSubmit={(e) => {
            e.preventDefault();
            setQuery({ course: normalizeFullCode(courseInput) });
          }}
        >
          <input
            placeholder="Course, e.g. CIS 1200"
            value={courseInput}
            onChange={(e) => setCourseInput(e.target.value)}
          />
          {courseCode &&
            (courseError
              ? courseError.status === 404
                ? "Course not found"
                : "Couldn't load course"
              : !course && "Loading...")}
        </CourseSearch>
      </Header>
      {error ? (
        <Message>{errorMessage(error)}</Message>
      ) : !selectedKeys && !planId ? (
        <Message>Pick one or more programs, or open a degree plan, to see their rule trees.</Message>
      ) : !programs ? (
        <Message>Loading programs...</Message>
      ) : (
        <DegreeExplorer
          programs={programs}
          course={courseError ? null : course ?? null}
          plan={planId ? planView?.overlay ?? null : null}
        />
      )}
    </Page>
  );
}
