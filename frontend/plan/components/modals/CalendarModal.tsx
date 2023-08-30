import React, { useEffect, useState } from "react";
import styled from "styled-components";
import { connect } from "react-redux";

const Outer = styled.div`
    overflow-x: hidden;
`;

const Row = styled.div`
    display: flex;
    align-items: center;
`;

const Col = styled.div`
    flex: 1;
    padding: 0;
`;

const BigText = styled.p`
    font-size: 14px;
    line-height: 1.5;
`;

const Button = styled.a`
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    margin: 0 5px;
    border-radius: 5px;
`;

const ICSButton = styled(Button)`
    background-color: #07aced;
`;

const CopyButton = styled(Button)`
    background-color: #2ce84f;
`;

const FixedInput = styled.input`
    height: 30px;
    flex: 1;
`;

const LoveFromLabs = styled.div`
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 20px;
`;

interface CalendarModalProps {
    schedulePk: number;
    clickedOnSchedule: number;
}

interface ToastProps {
    message: string;
    show: boolean;
}

const ToastWrapper = styled.div`
    position: fixed;
    bottom: 50px;
    left: 50%; 
    transform: translateX(-50%); 
    width: 330px;
    height: 30px;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #1e78e6;
    color: white;
    padding: 15px;
    border-radius: 5px;
    z-index: 1000;
    opacity: ${(props: { show: boolean }) => (props.show ? 1 : 0)};
    transition: opacity 0.5s ease-in, visibility 0.5s ease-in;
    visibility: ${(props: { show: boolean }) =>
        props.show ? "visible" : "hidden"};
`;

const Toast: React.FC<ToastProps> = ({ message, show }) => {
    return <ToastWrapper show={show}>{message}</ToastWrapper>;
};

const CalendarModal = ({
    schedulePk,
    clickedOnSchedule,
}: CalendarModalProps) => {
    const [url, setUrl] = useState<string>("INVALID");
    const [showToast, setShowToast] = useState<boolean>(false);
    const [toastMessage, setToastMessage] = useState<string>("");

    const showToastMessage = (message: string) => {
        setToastMessage(message);
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
    };

    useEffect(() => {
        const { hostname } = window.location;
        const protocol = hostname === "localhost" ? "http" : "https";
        const baseApiUrl = `${protocol}://${hostname}/api`;

        setUrl(`${baseApiUrl}/plan/${clickedOnSchedule}/calendar`);
    }, [schedulePk]);

    return (
        <Outer>
            <BigText>
                You can use the ICS URL below to import your schedule into a
                Google or macOS Calendar. This calendar will display all your
                classes and class times until the end of the semester.
                <br />
                <br />
                This link is personalized for your account, don't share it with
                others.
            </BigText>
            <Row>
                <Col>
                    <ICSButton>ICS URL</ICSButton>
                </Col>
                <Col>
                    <FixedInput
                        type="text"
                        readOnly
                        value={url}
                        onClick={(e) => (e.target as HTMLInputElement).select()}
                    />
                </Col>
                <Col>
                    <CopyButton
                        onClick={async () => {
                            try {
                                await navigator.clipboard.writeText(url);
                                showToastMessage(
                                    "Successfully copied to clipboard!"
                                );
                            } catch (error) {
                                showToastMessage(
                                    "Failed to copy! You need to manually copy the URL."
                                );
                            }
                        }}
                    >
                        Copy
                    </CopyButton>
                </Col>
            </Row>
            {showToast && <Toast message={toastMessage} show={showToast} />}
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

const mapStateToProps = (state: any) => ({
    clickedOnSchedule: state.schedule.clickedOnSchedule,
});

export default connect(mapStateToProps)(CalendarModal);
