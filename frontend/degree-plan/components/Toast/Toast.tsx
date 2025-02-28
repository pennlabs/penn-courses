import { createContext } from "react";
import { toast } from "react-toastify";

  
const ToastContext = createContext((text: string, error: boolean) => {});

export default ToastContext;