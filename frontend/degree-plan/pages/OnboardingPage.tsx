import React, { useState, useRef } from "react";
import styled from "@emotion/styled";
import useSWR from "swr";
import { pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";
import { DegreeListing, DegreePlan, MajorOption, SchoolOption } from "@/types";
import { polyfillPromiseWithResolvers } from "./polyfilsResolver";

import "core-js/full/promise/with-resolvers.js";

import { parseItems, parseTranscript, ParsedText, flattenParsedText } from "../utils/parseUtils";
import WelcomeLayout from "@/components/OnboardingPanels/WelcomePanel";
import CreateWithTranscriptPanel from "@/components/OnboardingPanels/CreateWithTranscriptPanel";

polyfillPromiseWithResolvers();

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/legacy/build/pdf.worker.min.mjs`;

const OnboardingPage = ({
  setShowOnboardingModal,
  setActiveDegreeplan,
}: {
  setShowOnboardingModal: (arg0: boolean) => void;
  setActiveDegreeplan: (arg0: DegreePlan) => void;
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

  const [PDF, setPDF] = useState<File | null>(null);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [scrapedCourses, setScrapedCourses] = useState<any>([]);
  const [currentPage, setCurrentPage] = useState<number>(0);

  const { data: degrees, isLoading: isLoadingDegrees } = useSWR<
    DegreeListing[]
  >(`/api/degree/degrees`);

  // TRANSCRIPT PARSING
  const total = useRef<Record<number, ParsedText[]>>({});
  const addText = (items: any[], index: number) => {
    const parsed = parseItems(items);
    total.current[index] = total.current[index] ?? [];
    total.current[index].push(parsed);

    // If all pages have been read, begin to parse text from transcript
    if (Object.keys(total.current).length === numPages) {
      let all: string[] = [];
      const sortedPageIndexes = Object.keys(total.current)
        .map((key) => Number(key))
        .sort((a, b) => a - b);

      sortedPageIndexes.forEach((pageIndex) => {
        const pageEntries = total.current[pageIndex];
        if (!pageEntries) return;
        pageEntries.forEach((pageText) => {
          all = all.concat(flattenParsedText(pageText));
        });
      });

      const {
        scrapedCourses,
        startYear,
        scrapedSchools,
        detectedMajorsOptions,
      } = parseTranscript(all, degrees);
      setScrapedCourses(scrapedCourses);
      console.log(scrapedCourses);
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
      transcriptDetected.current = startYear ? true : false;
    }
  };

  const transcriptDetected = useRef<boolean | null>(null);

  const resetParser = () => {
    total.current = {};
    transcriptDetected.current = null;
    setSchools([]);
    setMajors([]);
    setScrapedCourses([]);
    setStartingYear(null);
    setGraduationYear(null);
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
        startingYear={startingYear}
        setCurrentPage={setCurrentPage}
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
      setShowOnboardingModal={setShowOnboardingModal}
    />
  );
};

export default OnboardingPage;
