import React from 'react'
import withLayout from './withLayout'
import { ErrorBox } from '../components/common'

const ErrorMsg = () => <ErrorBox>404 Page Not Found</ErrorBox>

export const ErrorPage = withLayout(ErrorMsg)
