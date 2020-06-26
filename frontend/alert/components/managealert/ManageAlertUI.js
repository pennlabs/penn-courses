import React, { useState, useEffect } from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import Header from "./Header";
import { Flex } from "../common/layout";
import { AlertSearch } from "./AlertSearch";
import { AlertItem } from "./AlertItem";
import "./ManageAlert.module.css";
import { maxWidth, PHONE } from "../../constants";

const Container = styled.div`
    background: #ffffff;
    width: 80%;
    max-width: 80rem;
    box-shadow: 0 0.1rem 0.2rem 0 rgba(0, 0, 0, 0.08);
    flex-grow: 1;
    ${maxWidth(PHONE)} {
        width: 95%;
        padding: 0.25rem;
    }
`;

const TitleText = styled.p`
    color: #333333;
    font-size: 1.4rem;
    font-weight: bold;
    ${maxWidth(PHONE)} {
        font-size: 0.75rem;
    }
`;

const Grid = styled.div`
    display: grid;
    grid-template-columns: 1fr 3fr 2fr 2fr 3fr 2fr;
    grid-template-rows: 1.5rem;
    grid-auto-rows: 3rem;

    ${maxWidth(PHONE)} {
        grid-template-columns: 0fr 0fr 2fr 2fr 3fr 2fr;
        & > div:nth-child(6n + 1) {
            display: none;
        }
        & > div:nth-child(6n + 2) {
            display: none;
        }
    }
`;

// const Input = styled.input`
//     width: 16rem;
//     outline: none;
//     height: 1.8rem;
//     border: solid 0.5px #d6d6d6;
//     border-radius: 0.3rem 0rem 0rem 0.3rem;
//     font-size: 0.9rem;
//     padding-left: 0.5rem;
// `;

// const Button = styled.button`
//     outline: none;
//     height: 1.97rem;
//     width: 5rem;
//     border: solid 0.5px #489be8;
//     border-radius: 0rem 0.2rem 0.2rem 0rem;
//     background-color: #489be8;
//     color: #ffffff;
//     font-weight: 600;
//     font-size: 0.9rem;
//     cursor: pointer;
//     :hover {
//         background-color: #1496ed;
//     }
// `;

// const RightItemAlertFilter = styled(RightItem)`
//     & > * {
//         display: block;
//     }
// `;

export const ManageAlertHeader = () => (
    <Flex margin="-3.4rem 0rem 0rem 0rem">
        <img
            alt="Penn Course Alert logo"
            src="/svg/PCA_logo.svg"
            width="50rem"
        />

        {/*     <Flex> */}
        {/*         <Input placeholder="Course" /> */}
        {/*         <Button>Alert me</Button> */}
        {/*     </Flex> */}
        {/*     <P size="0.9rem" margin="1rem 0rem 0rem -3rem">Alert me until I cancel</P> */}
    </Flex>
);

export const ManageAlert = ({
    alerts,
    alertSel,
    setAlertSel,
    setFilter,
    actionButtonHandler,
    batchActionHandler,
    batchSelectHandler,
    batchSelected,
    setBatchSelected,
}) => {
    const toggleAlert = (id) => () => {
        setAlertSel({ ...alertSel, [id]: !alertSel[id] });
    };

    const [searchValue, setSearchValue] = useState("");
    const [searchTimeout, setSearchTimeout] = useState();
    const [numSelected, setNumSelected] = useState(0);

    useEffect(() => {
        setNumSelected(Object.values(alertSel).reduce((acc, x) => acc + x, 0));
    }, [alertSel]);

    const handleChange = (event) => {
        const searchText = event.target.value;
        setSearchValue(searchText);
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        setSearchTimeout(
            setTimeout(() => {
                setFilter({ search: searchText });
            }, 100)
        );
    };

    return (
        <Container>
            <Flex margin="0.2rem 2rem 0.1rem 2rem" center valign spaceBetween>
                <TitleText>Alert Management</TitleText>
                <AlertSearch value={searchValue} onChange={handleChange} />
            </Flex>
            <Grid>
                <Header
                    selected={numSelected}
                    batchSelected={batchSelected}
                    setBatchSelected={setBatchSelected}
                    batchActionHandler={batchActionHandler}
                    batchSelectHandler={batchSelectHandler}
                />
                {alerts.map((alert, i) => (
                    <AlertItem
                        key={alert.id}
                        checked={alertSel[alert.id]}
                        rownum={i + 2}
                        alertLastSent={alert.alertLastSent}
                        course={alert.section}
                        status={alert.status}
                        repeat={alert.repeat}
                        actions={alert.actions}
                        toggleAlert={toggleAlert(alert.id)}
                        actionButtonHandler={() =>
                            actionButtonHandler(alert.id, alert.actions)
                        }
                    />
                ))}
            </Grid>
        </Container>
    );
};

ManageAlert.propTypes = {
    alerts: PropTypes.arrayOf(PropTypes.object),
    actionButtonHandler: PropTypes.func,
    batchActionHandler: PropTypes.func,
    batchSelectHandler: PropTypes.func,
    batchSelected: PropTypes.bool,
    setBatchSelected: PropTypes.func,
    setAlertSel: PropTypes.func,
    setFilter: PropTypes.func,
    // alertSel is an object with potentially many fields, since it is used as a map
    // eslint-disable-next-line
    alertSel: PropTypes.object,
};
