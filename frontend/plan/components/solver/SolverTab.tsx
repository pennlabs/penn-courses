import React, { FunctionComponent } from "react";
import { connect, useSelector } from "react-redux";
import { ThunkDispatch } from "redux-thunk";
import styled from "styled-components";
import { addBreakItem, fetchCourseDetails, openModal } from "../../actions";
import { Section as SectionType, Break as BreakType, Schedule, Color } from "../../types";

const Box = styled.section<{ length: number }>`
    height: calc(100vh - 9em - 3em);
    border-radius: 4px;
    box-shadow: 0 5px 14px 0 rgba(0, 0, 0, 0.09);
    background-color: white;
    color: #4a4a4a;
    overflow: ${(props) => (props.length === 0 ? "hidden" : "auto")};
    flex-direction: column;
    padding: 0;
    display: flex;
    @media (max-width: 800px) {
        min-height: calc(100vh - 8em);
        height: 100%;
        box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.1);
    }

    &::-webkit-scrollbar {
        width: 0.5em;
        height: 0.5em;
    }

    &::-webkit-scrollbar-track {
        background: white;
    }

    &::-webkit-scrollbar-thumb {
        background: #95a5a6;
        border-radius: 1px;
    }
`;

interface SolverProps {
    contactInfo: { email: string; phone: string };
    manageBreaks?: {
        add: () => void;
    };
    mobileView: boolean;
}

const CartEmptyImage = styled.img`
    max-width: min(60%, 40vw);
`;

const BreakEmpty = () => (
    <div
        style={{
            fontSize: "0.8em",
            textAlign: "center",
            marginTop: "5vh",
        }}
    >
        <h3
            style={{
                fontWeight: "bold",
                marginBottom: "0.5rem",
            }}
        >
            You have no breaks!
        </h3>
        Click an icon to sign up for breaks.
        <br />
        <CartEmptyImage src="/icons/empty-state-cart.svg" alt="" />
    </div>
);


const Solver: React.FC<SolverProps> = ({
    manageBreaks,
    mobileView,
}) => {
    return(
        <Box length={1} id="breaks">
            {/* <DayTimeSelector
                // @ts-ignore
                filterData={filterData}
                updateCheckboxFilter={updateCheckboxFilter}
                checkboxProperty="days"
                // @ts-ignore
                startSearch={conditionalStartSearch}
                minRange={1.5}
                maxRange={17}
                step={1 / 60}
                updateRangeFilter={updateRangeFilter("time")}
                rangeProperty="time"
            /> */}
            <button onClick={manageBreaks?.add}>Add Break</button>
        </Box>
    );
};

const mapStateToProps = ({
}: any) => ({
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    manageBreaks: {
        add: () => {
            const newBreak = {
                name: "My Break",
                color: Color.RED,
                // location_string: "Library",
                meetings: [{
                    day: "M",
                    color: "#D0021B",
                    start: 10.15,
                    end: 11.44,
                    room: "DRL",
                    latitude: 10,
                    longitude: 10,
                    overlap: false,
                }],
            }
            dispatch(addBreakItem(newBreak));
        },
    },
});

export default connect(mapStateToProps, mapDispatchToProps)(Solver);
