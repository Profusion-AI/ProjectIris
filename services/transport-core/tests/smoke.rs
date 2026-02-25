use std::{net::UdpSocket, time::Duration};

use iris_transport_core::{
    framing::{now_ns, read_frame, write_frame, Frame},
    profile::LatencyProfile,
    transport::{
        connect_publisher, connect_subscriber, generate_self_signed_cert, run_relay, ClientConnect,
        RelayConfig,
    },
};

fn pick_port() -> u16 {
    let socket = UdpSocket::bind("127.0.0.1:0").expect("bind temp socket");
    socket.local_addr().expect("socket addr").port()
}

#[tokio::test]
async fn relay_smoke_realtime() {
    let dir = tempfile::tempdir().expect("temp dir");
    let cert_path = dir.path().join("relay-cert.pem");
    let key_path = dir.path().join("relay-key.pem");
    generate_self_signed_cert(&cert_path, &key_path).expect("generate cert");

    let addr = format!("127.0.0.1:{}", pick_port())
        .parse()
        .expect("socket addr");

    let relay = tokio::spawn(run_relay(RelayConfig {
        bind_addr: addr,
        cert_path: cert_path.clone(),
        key_path,
        required_control_token: None,
    }));

    tokio::time::sleep(Duration::from_millis(120)).await;

    let connect = ClientConnect {
        relay_addr: addr,
        server_name: "localhost".to_string(),
        ca_cert_path: cert_path,
        control_token: None,
    };

    let (_sub_ep, _sub_conn, mut recv) = connect_subscriber(&connect, 7, LatencyProfile::Realtime)
        .await
        .expect("subscriber connect");

    let (_pub_ep, _pub_conn, mut send) = connect_publisher(&connect, 7, LatencyProfile::Realtime)
        .await
        .expect("publisher connect");

    for i in 0..5u64 {
        let frame = Frame::data(7, i, now_ns(), vec![i as u8; 16]);
        write_frame(&mut send, &frame).await.expect("write frame");
    }

    let mut got = 0u64;
    while got < 5 {
        let frame = read_frame(&mut recv).await.expect("read frame");
        assert_eq!(frame.stream_id, 7);
        got += 1;
    }

    relay.abort();
}
