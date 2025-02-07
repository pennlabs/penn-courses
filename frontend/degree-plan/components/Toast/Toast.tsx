import { createContext } from "react";
import { toast } from "react-toastify";


function showToast(text: string, error: boolean) {
    if (error) {
      toast.error(text, {
        position: toast.POSITION.BOTTOM_CENTER,
      });
    } else {
      toast.success(text, {
        position: toast.POSITION.BOTTOM_CENTER,
      });
    }
  }
  
  
  
const ToastContext = createContext((text: string, error: boolean) => {});

export default ToastContext;