import React from "react";
import styled from "styled-components";
import {
    GridItem,
    Flex,
    RightItem,
} from "pcx-shared-components/src/common/layout";
import { Img } from "../common/common";
import { AlertAction } from "../../types";

const HeaderText = styled.p`
    font-size: 0.7rem;
    font-weight: bold;
    color: ${(props) => (props.color ? props.color : "#9ea0a7")};
`;

const HeaderAction = styled(HeaderText)`
    margin-right: 1rem;
    cursor: pointer;
`;

const HeaderButtonsFlex = styled(Flex)`
    & > * {
        display: block;
        margin-right: 0.4rem;
    }
`;

const HeaderRightItem = styled(RightItem)`
    margin-right: 0.5rem;
`;

interface HeaderProps {
    selected: number;
    batchActionHandler: (action: AlertAction) => void;
    batchSelectHandler: (select: boolean) => void;
    setBatchSelected: (select: boolean) => void;
    batchSelected: boolean;
}
// Component for table header in alert management
// Renders column titles or "x selected" depending
// on if alerts are selected
const Header = ({
    selected,
    batchActionHandler,
    batchSelectHandler,
    batchSelected,
    setBatchSelected,
}: HeaderProps) => {
    const headings = [
        "LAST NOTIFIED",
        "COURSE ID",
        "STATUS",
        "REPEAT",
        "ACTIONS",
    ];
    return (
        <>
            <GridItem column={1} row={1} color="#f8f8f8" halign valign>
                <input
                    type="checkbox"
                    checked={batchSelected}
                    onClick={() => {
                        batchSelectHandler(batchSelected);
                        setBatchSelected(!batchSelected);
                    }}
                />
            </GridItem>
            {selected === 0 &&
                headings.map((heading, i) => (
                    <GridItem
                        // eslint-disable-next-line
                        key={`header${i}`}
                        column={i + 2}
                        row={1}
                        color="#f8f8f8"
                        valign
                    >
                        <HeaderText>{heading}</HeaderText>
                    </GridItem>
                ))}

            {selected !== 0 && (
                <>
                    <GridItem column={2} row={1} color="#f8f8f8" valign>
                        <HeaderText color="#489be8">{`${selected} SELECTED`}</HeaderText>
                    </GridItem>
                    <GridItem column="3/7" row={1} color="#f8f8f8" valign>
                        <HeaderRightItem>
                            <HeaderButtonsFlex valign>
                                <Img
                                    src="/svg/abell.svg"
                                    width="0.5rem"
                                    height="0.5rem"
                                />
                                <HeaderAction
                                    onClick={() =>
                                        batchActionHandler(
                                            AlertAction.RESUBSCRIBE
                                        )
                                    }
                                >
                                    RESUBSCRIBE
                                </HeaderAction>
                            </HeaderButtonsFlex>
                            <HeaderButtonsFlex valign>
                                <Img
                                    src="/svg/bell-off.svg"
                                    width="0.5rem"
                                    height="0.5rem"
                                />
                                <HeaderAction
                                    onClick={() =>
                                        batchActionHandler(AlertAction.CANCEL)
                                    }
                                >
                                    CANCEL
                                </HeaderAction>
                            </HeaderButtonsFlex>
                            <HeaderButtonsFlex valign>
                                <Img
                                    src="/svg/trash.svg"
                                    width="0.5rem"
                                    height="0.5rem"
                                />
                                <HeaderAction
                                    onClick={() =>
                                        batchActionHandler(AlertAction.DELETE)
                                    }
                                >
                                    DELETE
                                </HeaderAction>
                            </HeaderButtonsFlex>
                        </HeaderRightItem>
                    </GridItem>
                </>
            )}
        </>
    );
};

export default Header;
