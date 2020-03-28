import React from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import Logo from "./assets/PCA_logo.svg";

const Container = styled.div`
    background: #ffffff;
    width: 80%;
    max-width: 80rem;
    min-height: 70%;
`;

const Flex = styled.div`
    display: flex;
    margin: ${(props) => props.margin};
    justify-content: ${(props) => (props.justify ? props.justify : "flex-start")};
    flex-direction: ${(props) => (props.col ? "column" : "row")};
`;

const RightItem = styled.div`
    margin-left: auto;
`;

const HeaderText = styled.p`
    font-size: 0.7rem;
    font-weight: bold;
    color: #9ea0a7;
`;

const TitleText = styled.p`
    color: #333333;
    font-size: 1.2rem;
    font-weight: bold;
`;

const Grid = styled.div`
    display: grid;
    grid-template-columns: 1fr 3fr 2fr 2fr 3fr 2fr;
`;

const GridItem = styled.div`
    grid-column: ${(props) => props.column};
    grid-row: ${(props) => props.row};
    background-color: ${(props) => (props.color ? props.color : "white")};
`;

const CenteredGridItem = styled(GridItem)`
    display: flex;
    align-items: center;
    justify-content: center;
`;

const Header = () => {
    const headings = ["LAST NOTIFIED", "COURSE ID", "STATUS", "REPEAT", "ACTIONS"];

    return (
        <>
            <CenteredGridItem column="1" row="1" color="#f8f8f8">
                <input type="checkbox" />
            </CenteredGridItem>
            {headings.map((heading, i) => (
                <GridItem column={(i + 2).toString()} row="1" color="#f8f8f8">
                    <HeaderText>{heading}</HeaderText>
                </GridItem>
            ))}

        </>
    );
};

export const ManageAlertHeader = () => (
    <Flex>
        <img
            alt="Penn Course Alert logo"
            src={Logo}
            width="50rem"
        />
    </Flex>
);


export const ManageAlert = () => {
    return (
        <Container>
            <Flex margin="0.7rem 2rem 0.7rem 2rem">
                <TitleText>Alert Management</TitleText>
                <RightItem>
                    <p>Sort by</p>
                </RightItem>
                <div>
                    <p>Search</p>
                </div>
            </Flex>
            <Grid>
                <Header />
            </Grid>
        </Container>
    );
};
