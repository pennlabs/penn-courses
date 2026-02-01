import { toast } from "react-toastify";

/* react toastify notifications */
export const toastWarn = (message: string) => {
    toast.warning(message, {
        position: "top-center",
        autoClose: 1700,
        hideProgressBar: true,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
    });
};

export const toastSuccess = (message: string) => {
    toast.success(message, {
        position: "top-center",
        autoClose: 1700,
        hideProgressBar: true,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
    });
};
