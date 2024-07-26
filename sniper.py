"use strict";

const tls = require("tls");
const WebSocket = require("ws");
const extractJsonFromString = require("extract-json-from-string");

let vanity;
const guilds = {};

const a = "NjE3NjUyNjM1MzE4NzQ3MTQ2.GkiBNk.MJH9WXSyrvxpHf9t6lpPynWUvmDfg9e2p9rBTA";
const l = "NjE3NjUyNjM1MzE4NzQ3MTQ2.GkiBNk.MJH9WXSyrvxpHf9t6lpPynWUvmDfg9e2p9rBTA";
const s = "1257305732466872352";
const i = "1259657477234884671";

const tlsSocket = tls.connect({
    host: "canary.discord.com",
    port: 443,
});

tlsSocket.on("data", async (data) => {
    const ext = await extractJsonFromString(data.toString());
    const find = ext.find((e) => e.code) || ext.find((e) => e.message);

    if (find) {
        console.log(find);

        const requestBody = JSON.stringify({
            content: `<@1106993943331217580> <@1225662201357144096> ${vanity} \n\`\`\`json\n${JSON.stringify(find)}\`\`\``,
        });

        const contentLength = Buffer.byteLength(requestBody);

        const requestHeader = [
            `POST /api/channels/${i}/messages HTTP/1.1`,
            "Host: canary.discord.com",
            `Authorization: ${l}`,
            "Content-Type: application/json",
            `Content-Length: ${contentLength}`,
            "",
            "",
        ].join("\r\n");
        const request = requestHeader + requestBody;
        tlsSocket.write(request);
    }
});

tlsSocket.on("error", (error) => {
    connectWebSocket();
});

tlsSocket.on("end", (event) => {
    connectWebSocket();
});

const connectWebSocket = () => {
    const websocket = new WebSocket("wss://gateway.discord.gg/");

    websocket.onclose = (event) => {
        connectWebSocket();
    };

    websocket.onmessage = async (message) => {
        const startMessage = process.hrtime();
        const { d, op, t } = JSON.parse(message.data);

        if (t === "GUILD_UPDATE") {
            const find = guilds[d.guild_id];
            if (find && find !== d.vanity_url_code) {
                const requestBody = JSON.stringify({ code: find });
                tlsSocket.write(
                    [
                        `PATCH /api/v7/guilds/${s}/vanity-url HTTP/1.1`,
                        "Host: canary.discord.com",
                        `Authorization: ${a}`,
                        "Content-Type: application/json",
                        `Content-Length: ${requestBody.length}`,
                        "",
                        "",
                    ].join("\r\n") + requestBody,
                );

                vanity = `${find} guild update `;
            }
        } else if (t === "GUILD_DELETE") {
            const find = guilds[d.id];
            if (find) {
                const requestBody = JSON.stringify({ code: find });
                tlsSocket.write(
                    [
                        `PATCH /api/v7/guilds/${s}/vanity-url HTTP/1.1`,
                        "Host: canary.discord.com",
                        `Authorization: ${a}`,
                        "Content-Type: application/json",
                        `Content-Length: ${requestBody.length}`,
                        "",
                        "",
                    ].join("\r\n") + requestBody,
                );
                vanity = `${find} guild **DELETE**`;
            }
        } else if (t === "READY") {
            d.guilds.forEach((guild) => {
                if (guild.vanity_url_code) {
                    guilds[guild.id] = guild.vanity_url_code;
                }
            });
            console.log(guilds);
        }

        if (op === 10) {
            websocket.send(
                JSON.stringify({
                    op: 2,
                    d: {
                        token: l,
                        intents: 1,
                        properties: {
                            os: "Linux",
                            browser: "Firefox",
                            device: "Firefox",
                        },
                    },
                }),
            );
            setInterval(
                () => websocket.send(JSON.stringify({ op: 1, d: null })),
                d.heartbeat_interval,
            );
        } else if (op === 7) {
            return connectWebSocket();
        }

        const endMessage = process.hrtime(startMessage);
        const elapsedMessageMillis = endMessage[0] * 1000 + endMessage[1] / 1e6;
        console.log(
            `Message handling time: ${elapsedMessageMillis.toFixed(3)}ms`,
        );
    };
};

tlsSocket.on("secureConnect", () => {
    connectWebSocket();

    setInterval(() => {
        tlsSocket.write(
            ["GET / HTTP/1.1", "Host: canary.discord.com", "", ""].join("\r\n"),
        );
    }, 600);
});
