import { Box, Button, CircularProgress, Fab, Typography } from "@mui/material";
import React, { useState } from "react";

const CircularProgressBar = ({value} : any) => {
    const [progress, setProgress] = React.useState(0);

    React.useEffect(() => {
        const timer = setInterval(() => {
            setProgress((prevProgress) => (prevProgress >= value * 25 ? prevProgress : prevProgress + 5));
        }, 90);

        return () => {
            clearInterval(timer);
        };
    }, []);

    return (
        <Box sx={{ position: 'relative', display: 'inline-flex' }}>
            <CircularProgress size={55} variant="determinate" value={progress} sx={{color: value > 2.0 ? '#5EA872' : '#4B9AE7'}}/>
            <Box
            sx={{
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                position: 'absolute',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
            }}
            >
            <Typography
                variant="caption"
                component="div"
                sx={{fontSize: 18}}
                // color="text.secondary"
            >{value}</Typography>
            </Box>
        </Box>
    )
}

export default CircularProgressBar;