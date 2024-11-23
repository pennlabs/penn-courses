import styled from "styled-components";
import { isMobile } from "react-device-detect";

const CourseCartItem = styled.div<{ $isMobile: boolean }>`
    background: white;
    transition: 250ms ease background;
    cursor: pointer;
    user-select: none;
    display: flex;
    align-items: center;
    padding: 0.8rem;
    border-bottom: 1px solid #e5e8eb;
    grid-template-columns: 20% 50% 15% 15%;
    * {
        user-select: none;
    }
    &:hover {
        background: #f5f5ff;
    }
    &:active {
        background: #efeffe;
    }

    &:hover i {
        color: #d3d3d8;
    }
`;

const CourseDetailsContainer = styled.div``;

const Dot = styled.span<{ $color: string }>`
    height: 5px;
    width: 5px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 10px;
    background-color: ${({ $color }) => $color};
`;

interface CourseDetailsProps {
    id: string;
    start: number;
    end: number;
    room: string;
    overlap: boolean;
}

const getTimeString = (start: number, end: number) => {
    const intToTime = (t: number) => {
        let hour = Math.floor(t % 12);
        const min = Math.round((t % 1) * 100);
        if (hour === 0) {
            hour = 12;
        }
        const minStr = min === 0 ? "00" : min.toString();
        return `${hour}:${minStr}`;
    };

    const startTime = intToTime(start);
    const endTime = intToTime(end);

    return `${startTime}-${endTime}`;
};

const CourseDetails = ({
    id,
    start,
    end,
    room,
    overlap,
}: CourseDetailsProps) => (
    <CourseDetailsContainer>
        <b>
            <span>{id.replace(/-/g, " ")}</span>
        </b>
        <div style={{ fontSize: "0.8rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
                <div>
                    {overlap && (
                        <div className="popover is-popover-right">
                            <i
                                style={{
                                    paddingRight: "5px",
                                    color: "#c6c6c6",
                                }}
                                className="fas fa-calendar-times"
                            />
                            <span className="popover-content">
                                Conflicts with schedule!
                            </span>
                        </div>
                    )}
                    {getTimeString(start, end)}
                </div>
                <div>{room ? room : "No room data"}</div>
            </div>
        </div>
    </CourseDetailsContainer>
);

interface CartSectionProps {
    id: string;
    color: string;
    start: number;
    end: number;
    room: string;
    overlap: boolean;
    focusSection: (id: string) => void;
}

function MapCourseItem({
    id,
    color,
    start,
    end,
    room,
    overlap,
    focusSection,
}: CartSectionProps) {
    return (
        <CourseCartItem
            role="switch"
            id={id}
            aria-checked="false"
            $isMobile={isMobile}
            onClick={() => {
                const split = id.split("-");
                focusSection(`${split[0]}-${split[1]}`);
            }}
        >
            <Dot $color={color} />
            <CourseDetails
                id={id}
                start={start}
                end={end}
                room={room}
                overlap={overlap}
            />
        </CourseCartItem>
    );
}

export default MapCourseItem;
