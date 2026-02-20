import useSWR from "swr";

const usePlatformOptions = () => {
    const { data: options, error } = useSWR(
        "https://platform.pennlabs.org/options/",
        (url) => fetch(url).then(res => res.json())
    );

    return { options, error };
};

export default usePlatformOptions;
