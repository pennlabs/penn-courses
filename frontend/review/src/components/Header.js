import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { HiBars3, HiXMark } from "react-icons/hi2";
import Collapse from "./common/Collapse";
import SearchBar from "./SearchBar";
import { Link, useHistory } from "react-router-dom";
import { useFilterDispatch } from "../utils/FilterContext";
import { maxWidth, minWidth } from "../styles/media";
import { linkStyles } from "../styles/mixins";

const HeaderContainer = styled.div`
  display: flex;
  align-items: center;
  width: 100%;
  height: 80px;
  background: white;
  border: 1px ${({ theme }) => theme.color.border.default} solid;
  z-index: 1000;
`;

const Title = styled.div`
  color: ${({ theme }) => theme.color.text.primary};
  font-size: 1.375rem;
  font-family: ${({ theme }) => theme.font.family.sans};
  font-weight: ${({ theme }) => theme.font.weight.regular};
  white-space: nowrap;

  ${maxWidth("md")} {
    font-size: 1.125rem;
  }

  ${maxWidth("sm")} {
    display: none;
  }
`;

const SearchBarContainer = styled.div`
  display: flex;
  flex: 1;
  width: 100%;
  max-width: 45vw;

  ${maxWidth("sm")} {
    max-width: 60vw;
  }

  ${maxWidth("xs")} {
    max-width: 30vw;
    min-width: 0;
  }
`;

const LinksContainer = styled.div`
  display: flex;
  margin-left: auto;
  margin-right: 30px;
  align-items: center;
  gap: 40px;
  font-family: ${({ theme }) => theme.font.family.sans};

  ${maxWidth("xl")} {
    display: none !important;
  }
`;

const MobileMenuWrapper = styled(Collapse)`
  width: 100%;
  background: ${({ theme }) => theme.color.surface.subtle};

  ${minWidth("xl")} {
    display: none; /* Hide mobile menu on desktop */
  }
`;

const MobileLinksInner = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 20px;
  font-size: 36px;
  font-weight: ${({ theme }) => theme.font.weight.regular};
  min-height: max-content;
`;

const StyledLink = styled.a`
  ${linkStyles}
`;

const StyledNavLink = styled(Link)`
  ${linkStyles}
`;

const Hamburger = styled.div`
  display: none;
  cursor: pointer;
  font-size: 30px;
  padding-left: 12px;
  margin-left: auto;
  margin-right: 28px;
  color: ${({ theme }) => theme.color.text.primary};

  ${maxWidth("xl")} {
    display: flex;
    align-items: center;
  }
`;

const Header = () => {
  const [isOpen, setIsOpen] = useState(false);

  const dispatch = useFilterDispatch();

  const getCourseCount = () =>
    Object.keys(localStorage).filter(a => !a.startsWith("meta-")).length;
  const [courseCount, setCourseCount] = useState(getCourseCount());

  useEffect(() => {
    const onStorageChange = () => setCourseCount(getCourseCount());
    window.addEventListener("storage", onStorageChange);
    window.onCartUpdated = onStorageChange;
    return () => {
      window.removeEventListener("storage", onStorageChange);
      window.onCartUpdated = null;
    };
  }, []);

  const history = useHistory();

  return (
    <>
      <HeaderContainer>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "15px",
            margin: "0 28px",
            cursor: "pointer"
          }}
          onClick={() => {
            if (window.location.pathname === "/") {
              // Already home so clicking the logo clears filters
              dispatch({ type: "RESET" });
            } else {
              history.push("/");
            }
          }}
        >
          <img
            src="/static/image/logo.png"
            alt="Penn Course Review"
            style={{ height: "35px", cursor: "pointer" }}
          />
          <Title>Penn Course Review</Title>
        </div>
        <SearchBarContainer>
          <SearchBar autoFocus={true}/>
        </SearchBarContainer>
        <LinksContainer>
          <StyledNavLink to="/about">About</StyledNavLink>
          <StyledNavLink to="/faq">FAQs</StyledNavLink>
          <StyledLink
            href="https://airtable.com/appFRa4NQvNMEbWsA/shrCCsGC2BjUif5Wx"
            target="_blank"
          >
            Feedback
          </StyledLink>
          <Link to="/cart" id="cart-icon" title="Course Cart">
            <i id="cart" className="fa fa-shopping-cart" />
            {courseCount > 0 && <span id="cart-count">{courseCount}</span>}
          </Link>
        </LinksContainer>
        <Hamburger onClick={() => setIsOpen(!isOpen)}>
          {isOpen ? <HiXMark /> : <HiBars3 />}
        </Hamburger>
      </HeaderContainer>
      <MobileMenuWrapper open={isOpen}>
        <MobileLinksInner>
          <StyledNavLink to="/about">About</StyledNavLink>
          <StyledNavLink to="/faq">FAQs</StyledNavLink>
          <StyledLink
            href="https://airtable.com/appFRa4NQvNMEbWsA/shrCCsGC2BjUif5Wx"
            target="_blank"
          >
            Feedback
          </StyledLink>
          <StyledNavLink to="/cart">Course Cart</StyledNavLink>
        </MobileLinksInner>
      </MobileMenuWrapper>
    </>
  );
};

export default Header;
