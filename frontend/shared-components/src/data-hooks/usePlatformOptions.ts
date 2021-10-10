import useSWR from "swr";

const usePlatformOptions = () => {
    const { data: options, error } = useSWR(
        "https://platform.pennlabs.org/options/"
    );

    return { options, error };
};

export default usePlatformOptions;
