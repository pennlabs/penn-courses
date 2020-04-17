import React from "react";
import styled from "styled-components";
// import PropTypes from "prop-types";
import Header from "./Header";
import Logo from "../../assets/PCA_logo.svg";
import { RightItem, P, Flex } from "./ManageAlertStyledComponents";
import { AlertSearch } from "./AlertSearch";
import { AlertItem } from "./AlertItem";
import { AlertAction, AlertStatus, AlertRepeat } from "./AlertItemEnums";
import "./ManageAlert.module.css";

const Container = styled.div`
    background: #ffffff;
    width: 80%;
    max-width: 80rem;
    min-height: 70%;
    box-shadow: 0 0.1rem 0.2rem 0 rgba(0, 0, 0, 0.08);
`;

const TitleText = styled.p`
    color: #333333;
    font-size: 1.4rem;
    font-weight: bold;
`;

const Grid = styled.div`
    display: grid;
    grid-template-columns: 1fr 3fr 2fr 2fr 3fr 2fr;
    grid-template-rows: 1.5rem;
    grid-auto-rows: 3rem;
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
    height: 1.97rem;
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

const RightItemAlertFilter = styled(RightItem)`
    & > * {
        display: block;
    }
`;

export const ManageAlertHeader = () => (
    <Flex margin="-3.4rem 0rem 0rem 0rem">
        <img
            alt="Penn Course Alert logo"
            src={Logo}
            width="50rem"
        />
        <Flex col center valign halign margin="1.5rem 1.5rem 1.5rem 2rem" padding="2.2rem 0rem 0rem 0rem">
            <Flex>
                <Input placeholder="Course" />
                <Button>Alert me</Button>
            </Flex>
            <P size="0.9rem" margin="1rem 0rem 0rem -3rem">Alert me until I cancel</P>
        </Flex>
    </Flex>
);

export const ManageAlert = ({ alerts }) => (
    <Container>
        <Flex margin="0.2rem 2rem 0.1rem 2rem" center valign halign>
            <TitleText>Alert Management</TitleText>
            <RightItemAlertFilter>
                <P size="0.7rem" margin="0rem 2rem 0rem 0rem">Sort by Last Notified</P>
                <AlertSearch />
            </RightItemAlertFilter>
        </Flex>
        <Grid>
            <Header />
            {alerts.map((alert,i) => {
                console.log(alert);
                return <AlertItem
                    rownum={i+2}
                    date={alert.date}
                    course={alert.section}
                    status={alert.status}
                    repeat={alert.repeat}
                    actions={alert.actions}
                />
            })}

        </Grid>
    </Container>
);
