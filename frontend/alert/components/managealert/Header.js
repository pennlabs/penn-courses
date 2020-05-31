import React from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import { AlertAction } from "./AlertItemEnums";
import { GridItem, Flex, RightItem } from "../common/layout";
import { Img } from "../common/common";

const HeaderText = styled.p`
    font-size: 0.7rem;
    font-weight: bold;
    color: ${props => (props.color ? props.color : "#9ea0a7")};
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

// Component for table header in alert management
// Renders column titles or "x selected" depending
// on if alerts are selected
const Header = ({
    selected,
    batchActionHandler,
    batchSelectHandler,
    batchSelected,
    setBatchSelected,
}) => {
    const headings = [
        "LAST NOTIFIED",
        "COURSE ID",
        "STATUS",
        "REPEAT",
        "ACTIONS",
    ];
    return (
        <>
            <GridItem column="1" row="1" color="#f8f8f8" halign valign>
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
                        column={(i + 2).toString()}
                        row="1"
                        color="#f8f8f8"
                        valign
                    >
                        <HeaderText>{heading}</HeaderText>
                    </GridItem>
                ))}

            {selected !== 0 && (
                <>
                    <GridItem column="2" row="1" color="#f8f8f8" valign>
                        <HeaderText color="#489be8">{`${selected} SELECTED`}</HeaderText>
                    </GridItem>
                    <GridItem column="3/7" row="1" color="#f8f8f8" valign>
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
                                            AlertAction.Resubscribe
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
                                        batchActionHandler(AlertAction.Cancel)
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
                                        batchActionHandler(AlertAction.Delete)
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

Header.propTypes = {
    selected: PropTypes.number,
    batchActionHandler: PropTypes.func,
    batchSelectHandler: PropTypes.func,
    setBatchSelected: PropTypes.func,
    batchSelected: PropTypes.bool,
};

export default Header;
