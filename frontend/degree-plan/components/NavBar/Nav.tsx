import React from 'react';
import Logo from './Logo';
import { type User } from '../../types'
import AccountIndicator from "pcx-shared-components/src/accounts/AccountIndicator";
import { useRouter } from "next/router";
import styled from "@emotion/styled"

const NavBarWrapper = styled.div`
  width: 100%;
  padding: 0 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0px 4px 4px rgba(0, 0, 0, 0.15);
  display: flex;
  justify-content: space-between;
`;

const Nav = ({ user }: { user: User }) => {
  const router = useRouter();
  return (
    <NavBarWrapper>
      <Logo/>
      <AccountIndicator
      leftAligned={false}
      user={user}
      pathname={router.pathname}
      />
    </NavBarWrapper>)
}

export default Nav;