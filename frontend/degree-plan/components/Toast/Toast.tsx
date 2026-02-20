import { createContext } from "react";
  
const ToastContext = createContext((text: string, error: boolean) => {});

export default ToastContext;