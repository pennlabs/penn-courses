import React from "react";
import styled from "styled-components";
import {
    GridItem,
    Flex,
} from "pcx-shared-components/src/common/layout";
import { Img } from "../common/common";
import { AlertAction } from "../../types";
import { maxWidth, PHONE, DESKTOP, between } from "../../constants";
import DropdownTool from "../common/DropdownTool";

const Grid = styled.div<{ $selected: boolean }>`
    display: grid;
    grid-template-columns: ${({ $selected: selected }) =>
        selected ? "1fr 10.5fr" : "1fr 1fr 3fr 1fr 1.5fr 1.25fr 2fr 1fr"};
    grid-template-rows: 1.75rem;

    ${maxWidth(PHONE)} {
        grid-template-columns: 0fr 0fr 2.5fr 2fr 0.5fr 3.5fr 0fr 1.5fr;
        & > div:nth-child(0) {
            display: none;
        }
        & > div:nth-child(8n + 1) {
            display: none;
        }
        & > div:nth-child(8n + 2) {
            display: none;
        }
        & > div:nth-child(8n + 7) {
            display: none;
        }
    }
`;

const HeaderText = styled.p`
    font-size: 0.7rem;
    font-weight: bold;
    color: ${(props) => (props.color ? props.color : "#9ea0a7")};
    text-align: center;
    margin: 0.25rem;

    ${between(PHONE, DESKTOP)} {
        font-size: 0.6rem;
    }
`;

const HeaderAction = styled(HeaderText)`
    margin-right: 1rem;
    color: #489be8;
    margin-left: 0rem;
`;

const HeaderButtonsFlex = styled(Flex)`
    margin-left: 0.5rem;
    cursor: pointer;
    & > * {
        display: block;

        margin-right: 0.4rem;
    }
`;

const HeaderContainer = styled.div`
    display: flex;
    align-items: center;

    ${maxWidth(PHONE)} {
        display: flex;
        align-items: center;
    }
`;

const Separator = styled.div`
    margin: 0rem 0.8rem 0rem 1.35rem;
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
        "",
        "SUBSCRIPTION",
        "NOTIFY WHEN CLOSED",
        "",
    ];

    return (
        <Grid $selected={selected !== 0}>
            <GridItem $column={1} $row={1} $color="#f8f8f8" $halign $valign $border>
                <input
                    type="checkbox"
                    checked={batchSelected}
                    onChange={() => {
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
                        $column={i + 2}
                        $row={1}
                        $color="#f8f8f8"
                        $valign
                        $halign
                        $border
                    >
                        <HeaderText>{heading}</HeaderText>
                    </GridItem>
                ))}
            {selected !== 0 && (
                <>
                    <GridItem $column={2} $row={1} $color="#f8f8f8" $valign>
                        <HeaderContainer>
                            <HeaderText color="#489be8">{`${selected} SELECTED`}</HeaderText>
                            <Separator style={{ color: "#878787" }}>
                                |
                            </Separator>
                            <DropdownTool
                                dropdownTitle={"ALERTS"}
                                dropdownOptionsText={[
                                    "Toggle On",
                                    "Toggle Off",
                                ]}
                                optionFunctions={[
                                    () =>
                                        batchActionHandler(AlertAction.ONALERT),
                                    () =>
                                        batchActionHandler(
                                            AlertAction.OFFALERT
                                        ),
                                ]}
                                width={"5.5"}
                                img={"/svg/bell.svg"}
                            />

                            <DropdownTool
                                dropdownTitle={"NOTIFY WHEN CLOSED"}
                                dropdownOptionsText={[
                                    "Toggle On",
                                    "Toggle Off",
                                ]}
                                optionFunctions={[
                                    () =>
                                        batchActionHandler(
                                            AlertAction.ONCLOSED
                                        ),
                                    () =>
                                        batchActionHandler(
                                            AlertAction.OFFCLOSED
                                        ),
                                ]}
                                width={"10.5"}
                                img={"/svg/bell.svg"}
                            />
                            <HeaderButtonsFlex
                                $valign
                                onClick={() =>
                                    batchActionHandler(AlertAction.DELETE)
                                }
                            >
                                <Img
                                    src="/svg/blue-trash.svg"
                                    width="0.75rem"
                                    height="0.75rem"
                                />
                                <HeaderAction>DELETE</HeaderAction>
                            </HeaderButtonsFlex>
                        </HeaderContainer>
                    </GridItem>
                </>
            )}
        </Grid>
    );
};

export default Header;
