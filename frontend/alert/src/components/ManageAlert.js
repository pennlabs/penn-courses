import React from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import Logo from "../assets/PCA_logo.svg";

const Container = styled.div`
    background: #ffffff;
    width: 80%;
    max-width: 80rem;
    min-height: 70%;
    box-shadow: 0 0.1rem 0.2rem 0 rgba(0, 0, 0, 0.08);
`;

const Flex = styled.div`
    display: flex;
    margin: ${(props) => props.margin};
    padding: ${(props) => props.padding};
    text-align: ${(props) => (props.center ? "center" : "initial")};
    justify-content: ${(props) => (props.center ? "center" : "initial")};
    align-items: ${(props) => (props.center ? "center" : "initial")};
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
    font-size: 1.4rem;
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

const Input = styled.input`
    width: 16rem;
    outline: none;
    height: 1.8rem;
    border: solid 0.5px #d6d6d6;
    border-radius: 0.3rem 0rem 0rem 0.3rem;
    font-size: 0.9rem;
    padding-left: 0.5rem;
`;

const Button = styled.button`
    outline: none;
    width: 5rem;
    border: solid 0.5px #489be8;
    border-radius: 0rem 0.2rem 0.2rem 0rem;
    background-color: #489be8;
    color: #ffffff;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    :hover {
        background-color: #1496ed;
    }
`;

const P = styled.p`
    font-size: ${(props) => props.size};
    margin: ${(props) => props.margin};
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
    <Flex margin="-3.4rem 0rem 0rem 0rem">
        <img
            alt="Penn Course Alert logo"
            src={Logo}
            width="50rem"
        />
        <Flex col center margin="1.5rem 1.5rem 1.5rem 2rem" padding="2.2rem 0rem 0rem 0rem">
            <Flex>
                <Input placeholder="Course" />
                <Button>Alert me</Button>
            </Flex>
            <P size="0.9rem" margin="1rem 0rem 0rem -3rem">Alert me until I cancel</P>
        </Flex>
    </Flex>
);

const ActionType = Object.freeze({Resubscribe: 0, Cancel: 1});

const ActionButton = (type) => {

}

const AlertItem = (date, course, status, repeat, actions, rownum) => {
    return (
        <>
            <CenteredGridItem column="1" row={rownum} />
        </>
    );
};


export const ManageAlert = () => {
    return (
        <Container>
            <Flex margin="0.4rem 2rem 0.4rem 2rem" center>
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
