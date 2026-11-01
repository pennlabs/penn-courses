import React, { useState, useRef, useEffect } from "react";
import styled from "@emotion/styled";
import useSWR from "swr";
import { pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";
import { DegreeListing, DegreePlan, Major, MajorOption, SchoolOption } from "@/types";
import { polyfillPromiseWithResolvers } from "./polyfilsResolver";

import "core-js/full/promise/with-resolvers.js";

import {
  parseItems,
  parseTranscript,
  ParsedText,
  flattenParsedText,
  MajorOptionItem,
} from "../utils/parseUtils";
import WelcomeLayout from "@/components/OnboardingPanels/WelcomePanel";
import CreateWithTranscriptPanel from "@/components/OnboardingPanels/CreateWithTranscriptPanel";

polyfillPromiseWithResolvers();

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/legacy/build/pdf.worker.min.mjs`;

const OnboardingPage = ({
  setShowOnboardingModal,
  setActiveDegreeplan,
  canExit = false,
}: {
  setShowOnboardingModal: (arg0: boolean) => void;
  setActiveDegreeplan: (arg0: DegreePlan) => void;
  canExit?: boolean;
}) => {
  const [startingYear, setStartingYear] = useState<{
    label: any;
    value: number;
  } | null>(null);
  const [graduationYear, setGraduationYear] = useState<{
    label: any;
    value: number;
  } | null>(null);
  const [schools, setSchools] = useState<SchoolOption[]>([]);
  const [majors, setMajors] = useState<MajorOption[]>([]);
  const [secondMajors, setSecondMajors] = useState<MajorOptionItem[]>([]);

  const [PDF, setPDF] = useState<File | null>(null);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [scrapedCourses, setScrapedCourses] = useState<any>([]);
  const [currentPage, setCurrentPage] = useState<number>(0);

  const { data: degrees } = useSWR<DegreeListing[]>(`/api/degree/degrees`);
  const { data: standaloneMajors } = useSWR<Major[]>(`/api/degree/majors`);
  // Matching a transcript's majors needs both lists. They are requested when this page mounts,
  // but a transcript can be uploaded and read before they arrive.
  const programsLoaded = degrees !== undefined && standaloneMajors !== undefined;

  // TRANSCRIPT PARSING
  const total = useRef<Record<number, ParsedText>>({});
  // True once every page of the uploaded PDF has been read.
  const [pagesRead, setPagesRead] = useState(false);
  // Guards against parsing the same upload twice when the program lists revalidate.
  const parsed = useRef(false);

  const addText = (items: any[], index: number) => {
    total.current[index] = parseItems(items);
    if (Object.keys(total.current).length === numPages) setPagesRead(true);
  };

  // Parse the transcript once its pages are read and the program lists are here, whichever
  // comes last. Parsing as soon as the pages were read used to run the major matching against
  // lists that had not loaded on a slow connection, which detected no majors and left the
  // major picker empty.
  useEffect(() => {
    if (!pagesRead || !programsLoaded || parsed.current) return;
    parsed.current = true;

    let all: string[] = [];
    const sortedPageIndexes = Object.keys(total.current)
      .map((key) => Number(key))
      .sort((a, b) => a - b);

    sortedPageIndexes.forEach((pageIndex) => {
      const pageEntry = total.current[pageIndex];
      if (!pageEntry) return;
      all = all.concat(flattenParsedText(pageEntry));
    });

    const {
      scrapedCourses,
      startYear,
      scrapedSchools,
      detectedMajorsOptions,
      detectedSecondMajorOptions,
    } = parseTranscript(all, degrees, standaloneMajors);
    setScrapedCourses(scrapedCourses);
    setStartingYear({
      value: startYear,
      label: startYear,
    });
    setGraduationYear({
      value: startYear + 4,
      label: startYear + 4,
    });
    setSchools(scrapedSchools);
    setMajors(detectedMajorsOptions);
    setSecondMajors(detectedSecondMajorOptions);
    transcriptDetected.current = startYear ? true : false;
  }, [pagesRead, programsLoaded, degrees, standaloneMajors]);

  const transcriptDetected = useRef<boolean | null>(null);

  const resetParser = () => {
    total.current = {};
    parsed.current = false;
    setPagesRead(false);
    transcriptDetected.current = null;
    setSchools([]);
    setMajors([]);
    setSecondMajors([]);
    setScrapedCourses([]);
    setStartingYear(null);
    setGraduationYear(null);
  };

  const exitOnboarding = () => {
    resetParser();
    setCurrentPage(0);
    setShowOnboardingModal(false);
  };

  if (currentPage === 0)
    return (
      <WelcomeLayout
        resetParser={resetParser}
        setNumPages={setNumPages}
        numPages={numPages}
        PDF={PDF}
        setPDF={setPDF}
        addText={addText}
        transcriptDetected={transcriptDetected}
        waitingForPrograms={pagesRead && !programsLoaded}
        startingYear={startingYear}
        setCurrentPage={setCurrentPage}
        canExit={canExit}
        onExit={exitOnboarding}
      />
    );

  return (
    <CreateWithTranscriptPanel
      inputtedStartingYear={startingYear}
      inputtedGraduationYear={graduationYear}
      scrapedCourses={scrapedCourses}
      setCurrentPage={setCurrentPage}
      setActiveDegreeplan={setActiveDegreeplan}
      inputtedSchools={schools}
      inputtedMajors={majors}
      inputtedSecondMajors={secondMajors}
      setShowOnboardingModal={setShowOnboardingModal}
      canExit={canExit}
      onExit={exitOnboarding}
    />
  );
};

export default OnboardingPage;
