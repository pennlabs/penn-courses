import { ArrowRightIcon, UploadIcon } from "@radix-ui/react-icons";
import { Dispatch, MutableRefObject, SetStateAction } from "react";
import { Document, Page } from "react-pdf";
import {
    CenteredFlexContainer,
    ChooseContainer,
    ContainerGroup,
    ErrorText,
    NextButton,
    TextButton,
    Upload,
} from "./SharedComponents";

type WelcomeLayoutProps = {
    resetParser: () => void;
    setNumPages: Dispatch<SetStateAction<number | null>>;
    numPages: number | null;
    setPDF: Dispatch<SetStateAction<any>>;
    PDF: any;
    addText: (items: any, index: number) => void;
    transcriptDetected: MutableRefObject<boolean | null>;
    startingYear: { label: any; value: number } | null;
    setCurrentPage: Dispatch<SetStateAction<number>>;
};

export default function WelcomeLayout({
    resetParser,
    setNumPages,
    numPages,
    setPDF,
    PDF,
    addText,
    transcriptDetected,
    startingYear,
    setCurrentPage,
}: WelcomeLayoutProps) {
    return (
        <CenteredFlexContainer>
            <ChooseContainer $maxWidth="90%" $minWidth="90%">
                <div style={{ display: "none" }}>
                    <Document
                        file={PDF}
                        onLoadSuccess={(pdf) => {
                            resetParser();
                            setNumPages(pdf.numPages);
                        }}
                    >
                        {Array.from(new Array(numPages), (el, index) => (
                            <Page
                                key={`page_${index + 1}`}
                                pageNumber={index + 1}
                                onGetTextSuccess={({ items, styles }) => {
                                    addText(items, index);
                                }}
                                renderTextLayer={true}
                            />
                        ))}
                    </Document>
                </div>

                <h1>Welcome to Penn Degree Plan!</h1>
                <ContainerGroup>
                    <label>
                        <input
                            type="file"
                            accept=".pdf"
                            hidden
                            onChange={(event) => {
                                if (event.target.files)
                                    setPDF(event.target.files[0]);
                            }}
                        />
                        <Upload>
                            <p style={{ fontSize: "1.2rem" }}>
                                Upload Transcript
                            </p>
                            {PDF?.name ? (
                                <p>{PDF?.name}</p>
                            ) : (
                                <UploadIcon width={20} height={20} />
                            )}
                        </Upload>
                    </label>
                    <ErrorText>
                        {PDF &&
                            transcriptDetected.current !== null &&
                            (transcriptDetected.current === true
                                ? ""
                                : "Can't detect a transcript! Try another file.")}
                    </ErrorText>
                    <NextButton
                        onClick={() => {
                            if (startingYear && startingYear?.value !== 0)
                                setCurrentPage(1);
                        }}
                        disabled={
                            PDF && transcriptDetected.current === true
                                ? false
                                : true
                        }
                        style={{
                            height: "45px",
                            width: "100px",
                            borderRadius: "7px",
                            color: PDF ? "white" : "",
                            transition: "all 0.25s",
                        }}
                    >
                        Next
                    </NextButton>
                </ContainerGroup>
                <TextButton
                    onClick={() => {
                        resetParser();
                        setCurrentPage(2);
                    }}
                    style={{ borderBottom: "1px solid #aaa" }}
                >
                    <p>Enter information manually</p>
                    <ArrowRightIcon />
                </TextButton>
            </ChooseContainer>
        </CenteredFlexContainer>
    );
}
