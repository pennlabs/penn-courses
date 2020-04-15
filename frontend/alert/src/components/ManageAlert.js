import React from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import Logo from "../assets/PCA_logo.svg";
import Bell from "../assets/bell.svg";
import XBell from "../assets/bell-off.svg";
import Search from "../assets/search.svg";
import styles from "./ManageAlert.module.css";

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
    text-align: ${(props) => (props.center ? "center" : null)};
    align-items: ${(props) => (props.valign ? "center" : null)};
    justify-content: ${(props) => (props.halign ? "center" : null)};
    flex-direction: ${(props) => (props.col ? "column" : "row")};
`;

const ActionFlex = styled(Flex)`
    background-color: ${(props) => props.background};
    border-radius: 0.2rem;
    cursor: pointer;
`;

const SearchFlex = styled(Flex)`
    background-color: #f4f4f4;
    border: solid 0.5px #dfe3e8;
    border-radius: 0.2rem;
`;

const SearchInput = styled.input`
    background-color: transparent;
    border: none;
    outline: none;
    width: 10rem;
`;

const RightItem = styled.div`
    display: flex;
    align-items: center;
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
    grid-template-rows: 1.5rem;
    grid-auto-rows: 3rem;
`;

const GridItem = styled.div`
    display: flex;
    align-items: ${(props) => (props.valign ? "center" : null)};
    justify-content: ${(props) => (props.halign ? "center" : null)};
    grid-column: ${(props) => props.column};
    grid-row: ${(props) => props.row};
    background-color: ${(props) => (props.color ? props.color : "white")};
    border-bottom: ${(props) => (props.border ? "1px solid #ececec" : null)};
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

const P = styled.p`
    font-size: ${(props) => props.size};
    font-weight: ${(props) => props.weight};
    color: ${(props) => props.color};
    margin: ${(props) => props.margin};
`;

const StatusInd = styled.div`
    border-radius: 1rem;
    width: 0.4rem;
    height: 0.4rem;
    background-color: ${(props) => props.background};
`;

const Img = styled.img`
    width: ${(props) => props.width};
    height: ${(props) => props.height};
`;

const Header = () => {
    const headings = ["LAST NOTIFIED", "COURSE ID", "STATUS", "REPEAT", "ACTIONS"];

    return (
        <>
            <GridItem column="1" row="1" color="#f8f8f8" halign valign>
                <input type="checkbox" />
            </GridItem>
            {headings.map((heading, i) => (
                <GridItem key={`header${i}`} column={(i + 2).toString()} row="1" color="#f8f8f8" valign>
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
        <Flex col center valign halign margin="1.5rem 1.5rem 1.5rem 2rem" padding="2.2rem 0rem 0rem 0rem">
            <Flex>
                <Input placeholder="Course" />
                <Button>Alert me</Button>
            </Flex>
            <P size="0.9rem" margin="1rem 0rem 0rem -3rem">Alert me until I cancel</P>
        </Flex>
    </Flex>
);

const AlertSearch = () => (
    <SearchFlex valign>
        <Flex valign margin="0.2rem" className={styles.search}>
            <Img src={Search} alt="" width="0.6rem" height="0.6rem" />
            <SearchInput type="search" placeholder="Search" />
        </Flex>
    </SearchFlex>
);

const AlertAction = Object.freeze({ Resubscribe: 1, Cancel: 2 });
const AlertStatus = Object.freeze({ Closed: 1, Open: 2 });
const AlertRepeat = Object.freeze({ Inactive: 1, EOS: 2, Once: 3 });

const ActionButton = ({ type }) => {
    let img;
    let primary;
    let secondary;
    let text;

    switch (type) {
        case 1:
            primary = "#5891fc";
            secondary = "rgba(88, 145, 252, 0.12)";
            img = Bell;
            text = "Resubscribe";
            break;
        case 2:
            primary = "#646e7a";
            secondary = "rgba(162, 169, 176, 0.15)";
            img = XBell;
            text = "Cancel";
            break;
        default:
    }

    return (
        <ActionFlex valign halign background={secondary}>
            <Flex valign margin="0.3rem" className={styles.actionbutton}>
                <P size="0.6rem" color={primary} weight="600">{text}</P>
                <Img src={img} width="0.6rem" height="0.6rem" alt="" />
            </Flex>
        </ActionFlex>
    );
};



const AlertItem = ({ date, course, status, repeat, actions, rownum }) => {
    let statustext;
    let statuscolor;
    let alerttext;
    let alertcolor;

    switch (status) {
        case 1:
            statustext = "Closed";
            statuscolor = "#e1e6ea";
            break;
        case 2:
            statustext = "Open";
            statuscolor = "#78d381";
            break;
        default:
    }

    switch (repeat) {
        case 1:
            alerttext = "Inactive";
            alertcolor = "#b2b2b2";
            break;
        case 2:
            alerttext = "Until end of semester";
            alertcolor = "#333333";
            break;
        case 3:
            alerttext = "Once";
            alertcolor = "#333333";
            break;
        default:
    }




    return (
        <>
            <GridItem column="1" row={rownum} border halign valign>
                <input type="checkbox" />
            </GridItem>
            <GridItem column="2" row={rownum} border valign>
                <P size="0.7rem">{date}</P>
            </GridItem>
            <GridItem column="3" row={rownum} border valign>
                <P size="0.7rem">{course}</P>
            </GridItem>
            <GridItem column="4" row={rownum} border valign className={styles.status}>
                <StatusInd background={statuscolor} />
                <P size="0.7rem">{statustext}</P>
            </GridItem>
            <GridItem column="5" row={rownum} border valign>
                <P size="0.7rem" color={alertcolor}>{alerttext}</P>
            </GridItem>
            <GridItem border column="6" row={rownum} valign>
                <ActionButton type={actions} />
            </GridItem>
        </>
    );
};


export const ManageAlert = () => {
    return (
        <Container>
            <Flex margin="0.2rem 2rem 0.1rem 2rem" center valign halign>
                <TitleText>Alert Management</TitleText>
                <RightItem className={styles.alertmodifiers} >
                    <P size="0.7rem" margin="0rem 2rem 0rem 0rem">Sort by Last Notified</P>
                    <AlertSearch />
                </RightItem>
            </Flex>
            <Grid>
                <Header />
                <AlertItem
                    rownum={2}
                    date="9/12/2017 at 6:30PM"
                    course="CIS-120-001"
                    status={AlertStatus.Open}
                    repeat={AlertRepeat.Inactive}
                    actions={AlertAction.Cancel}
                />
                <AlertItem
                    rownum={3}
                    date="9/12/2017 at 6:30PM"
                    course="CIS-120-001"
                    status={AlertStatus.Closed}
                    repeat={AlertRepeat.EOS}
                    actions={AlertAction.Resubscribe}
                />               
            </Grid>
        </Container>
    );
};
