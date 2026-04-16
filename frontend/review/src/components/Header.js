import React, { useState } from 'react';
import styled from 'styled-components';
import { HiBars3, HiXMark } from "react-icons/hi2";
import { motion } from 'motion/react';
import NewSearchBar from './NewSearchBar';
import { useHistory } from 'react-router-dom';

const HeaderContainer = styled.div`
    display: flex;
    align-items: center;
    width: 100%;
    height: 80px;
    background: white;
    border: 1px #EBEEF2 solid;
    z-index: 1000;
`;

const Title = styled.div`
    color: #545454;
    font-size: 1.375rem;
    font-family: 'SFPro', sans-serif;
    font-weight: 410;
    white-space: nowrap;

    @media (max-width: 800px) {
        font-size: 1.125rem;
    }
    
    @media (max-width: 700px) {
        display: none;
    }
`;

const SearchBarContainer = styled.div`
    display: flex;
    flex: 1;
    width: 100%;
    max-width: 45vw;

    @media(max-width: 700px) {
        max-width: 60vw;
    }

    @media (max-width: 300px) {
        max-width: 30vw;
        min-width: 0;
    }
`;

const LinksContainer = styled(motion.div)`
    display: flex;
    margin-left: auto;
    margin-right: 60px;
    align-items: center;
    gap: 40px;
    font-family: 'SFPro', sans-serif;

    @media(max-width: 1200px) {
        display: none !important;

    }

`;

const MobileMenuWrapper = styled(motion.div)`
    overflow: hidden;
    width: 100%;
    background: #F7F9FB;

    @media (min-width: 1201px) {
        visibility: hidden !important; /* Hide mobile menu on desktop */
        height: 0 !important;
    }
`;

const MobileLinksInner = styled(motion.div)`
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
    padding: 20px;
    font-size: 36px;
    font-weight: 410;
    min-height: max-content;
`;

const StyledLink = styled.a`
    text-decoration: none;
    color: #545454;
    font-size: 16px;

    &:hover {
        color: #000000;
        text-decoration: none;
    }
`;

const Hamburger = styled.div`
    display: none; 
    cursor: pointer;
    font-size: 30px;
    padding-left: 12px;
    margin-left: auto;
    margin-right: 28px;
    color: #545454;

    @media (max-width: 1200px) {
        display: flex; 
        align-items: center;
    }
`;

const menuVariants = {
    open: { 
        height: 'auto',
        opacity: 1, 
        transition: { type: 'spring', stiffness: 300, damping: 30 }
    },
    closed: { 
        height: 0,
        opacity: 0, 
        transition: { 
            height: { type: 'spring', stiffness: 300, damping: 30 },
            opacity: { duration: 0.2 } 
        }
    }
};

const Header = () => {
    const [isOpen, setIsOpen] = useState(false);

    const history = useHistory();

    return (
        <>
        <HeaderContainer>
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px', margin: '0 28px' }}>
                <img
                    src="/static/image/logo.png" alt="Penn Course Review" style={{ height: '35px', cursor: 'pointer' }}
                    onClick={() => history.push('/')}
                />
                <Title>Penn Course Review</Title>
            </div>
            <SearchBarContainer>
                <NewSearchBar isTitle={true} />
            </SearchBarContainer>
            <LinksContainer>
                <StyledLink href='/about'>About</StyledLink>
                <StyledLink href='/faq'>FAQs</StyledLink>
                <StyledLink href='https://airtable.com/appFRa4NQvNMEbWsA/shrCCsGC2BjUif5Wx' target="_blank">Feedback</StyledLink>
            </LinksContainer>
            <Hamburger onClick={() => setIsOpen(!isOpen)}>
                {isOpen ? <HiXMark /> : <HiBars3 />}
            </Hamburger>
        </HeaderContainer>
        <MobileMenuWrapper
            initial={false}
            animate={isOpen ? "open" : "closed"}
            variants={menuVariants}
        >
            <MobileLinksInner>
                <StyledLink href='/about'>About</StyledLink>
                <StyledLink href='/faq'>FAQs</StyledLink>
                <StyledLink href='https://airtable.com/appFRa4NQvNMEbWsA/shrCCsGC2BjUif5Wx' target="_blank">Feedback</StyledLink>
            </MobileLinksInner>
        </MobileMenuWrapper>
        </>
    )
}

export default Header;