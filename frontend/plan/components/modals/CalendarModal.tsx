import React, { useEffect, useState } from "react";
import { toast } from "react-toastify";
import styled from "styled-components";

interface RowProps {
    $align?: "flex-start" | "flex-end" | "center" | "baseline" | "stretch";
}

const Row = styled.div<RowProps>`
    display: flex;
    flex-wrap: wrap;
    align-items: ${(props) => props.$align || "stretch"};
`;

interface ColProps {
    $span?: number;
}

const Outer = styled.div`
    overflow-x: hidden;
`;

const Col = styled.div<ColProps>`
    flex: ${(props) => props.$span || 1};
    padding: 0;
    box-sizing: border-box;
`;

const LoveFromLabs = styled.div`
    display: flex;
    align-items: center;
    justify-content: center;
`;

const BigText = styled.p`
    font-size: 14px;
    line-height: 1.5;
`;

const FixedInput = styled.input`
    display: flex;
    position: relative;
    top: 10px;
    margin: 0;
`

interface CalendarModalProps {
    $schedulePk: number;
}

const CalendarModal = ({ $schedulePk: schedulePk }: CalendarModalProps) => {
    const [url, setUrl] = useState<string>("INVALID");

    useEffect(() => {
        setUrl(`http://penncourseplan.com/api/plan/${schedulePk}/calendar`);
    }, []);

    return (
        <Outer>
            <BigText>
                You can use the ICS URL below to import your schedule into a Google or macOS Calendar. This
                calendar will display all your classes and class times until the
                end of the semester.
                <br />
                <br />
                This link is personalized for your account, don't share it with
                others.
            </BigText>
            <br />
            <Row $align="center" className="row field has-addons is-expanded">
                <Col className="col control">
                    <a className="button is-static">ICS URL</a>
                </Col>
                <Col $span={8}>
                    <FixedInput
                        type="text"
                        readOnly
                        value={url}
                        onClick={(e) => (e.target as HTMLInputElement).select()}
                    />
                </Col>
                <Col className="col control">
                    <a
                        className="button is-info"
                        onClick={async () => {
                            try {
                                await navigator.clipboard.writeText(url);
                                toast.info("Copied to clipboard!");
                            } catch (error) {
                                toast.error(
                                    "Failed to copy! You need to manually copy the URL."
                                );
                            }
                        }}
                    >
                        Copy
                    </a>
                </Col>
            </Row>

            <hr />

            <Row className="columns has-text-centered">
                <div className="column">
                    <h3><b>Import to Google Calendar</b></h3>
                    <BigText>
                        Use the URL above to import to Google Calendar. Need
                        help?
                        <br />
                        <a
                            href="https://support.google.com/calendar/answer/37100#add_via_link"
                            target="_blank"
                            rel="noreferrer noopener"
                        >
                            Check out this guide!
                        </a>
                    </BigText>
                </div>
                <div className="column">
                    <h3><b>Import to macOS Calendar</b></h3>
                    <BigText>
                        Use the URL above to import to the macOS Calendar app.
                        Need help?
                        <br />
                        <a
                            href="https://support.apple.com/guide/calendar/subscribe-to-calendars-icl1022/mac"
                            target="_blank"
                            rel="noreferrer noopener"
                        >
                            Check out this guide!
                        </a>
                    </BigText>
                </div>
            </Row>
            <LoveFromLabs>
                With <i className="fa fa-heart" style={{ color: "red" }} />
                <br />{" "}
                <a
                    href="//pennlabs.org"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Penn Labs
                </a>
            </LoveFromLabs>
        </Outer>
    );
};

export default CalendarModal;
